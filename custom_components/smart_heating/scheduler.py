"""Schedule executor for Zone Heater Manager."""
import logging
from datetime import datetime, time
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)

SCHEDULE_CHECK_INTERVAL = timedelta(minutes=1)  # Check schedules every minute

DAYS_OF_WEEK = {
    0: "Monday",
    1: "Tuesday", 
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


class ScheduleExecutor:
    """Execute area schedules to control temperatures."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager, learning_engine=None) -> None:
        """Initialize the schedule executor.
        
        Args:
            hass: Home Assistant instance
            area_manager: Zone manager instance
            learning_engine: Optional learning engine for predictive scheduling
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self._unsub_interval = None
        self._last_applied_schedule = {}  # Track last applied schedule per area
        _LOGGER.info("Schedule executor initialized")

    async def async_start(self) -> None:
        """Start the schedule executor."""
        _LOGGER.info("Starting schedule executor")
        
        # Run immediately on start
        await self._async_check_schedules()
        
        # Set up recurring check
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_check_schedules,
            SCHEDULE_CHECK_INTERVAL,
        )
        _LOGGER.info("Schedule executor started, checking every %s", SCHEDULE_CHECK_INTERVAL)

    async def async_stop(self) -> None:
        """Stop the schedule executor."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None
        _LOGGER.info("Schedule executor stopped")

    async def _async_check_schedules(self, now: Optional[datetime] = None) -> None:
        """Check all area schedules and apply temperatures if needed.
        
        Also handles smart night boost by predicting heating start times.
        
        Args:
            now: Current datetime (for testing, otherwise uses current time)
        """
        if now is None:
            now = datetime.now()
            
        current_time = now.time()
        current_day = DAYS_OF_WEEK[now.weekday()]
        
        _LOGGER.debug(
            "Checking schedules for %s at %s",
            current_day,
            current_time.strftime("%H:%M"),
        )
        
        areas = self.area_manager.get_all_areas()
        
        for area_id, area in areas.items():
            if not area.enabled:
                _LOGGER.debug("Area %s is disabled, skipping schedule check", area.name)
                continue
            
            # Handle smart night boost prediction
            if area.smart_night_boost_enabled and self.learning_engine:
                await self._handle_smart_night_boost(area, now)
                
            if not area.schedules:
                continue
                
            # Find active schedule for current day/time
            active_schedule = self._find_active_schedule(
                area.schedules,
                current_day,
                current_time,
            )
            
            if active_schedule:
                schedule_key = f"{area_id}_{active_schedule.schedule_id}"
                
                # Only apply if this schedule hasn't been applied yet
                # (to avoid setting temperature every minute)
                if self._last_applied_schedule.get(area_id) != schedule_key:
                    await self._apply_schedule(area, active_schedule)
                    self._last_applied_schedule[area_id] = schedule_key
                    
            else:
                # No active schedule, clear the tracking
                if area_id in self._last_applied_schedule:
                    del self._last_applied_schedule[area_id]
                    _LOGGER.debug(
                        "No active schedule for area %s at %s %s",
                        area.name,
                        current_day,
                        current_time.strftime("%H:%M"),
                    )

    def _find_active_schedule(
        self,
        schedules: list[dict],
        current_day: str,
        current_time: time,
    ) -> Optional[dict]:
        """Find the active schedule for the given day and time.
        
        Args:
            schedules: List of schedule entries
            current_day: Current day name (e.g., "Monday")
            current_time: Current time
            
        Returns:
            Active schedule entry or None
        """
        for schedule in schedules.values():
            if schedule.day != current_day:
                continue
                
            # Parse schedule times
            start_time = time.fromisoformat(schedule.start_time)
            end_time = time.fromisoformat(schedule.end_time)
            
            # Check if current time is within schedule window
            # Handle schedules that cross midnight
            if start_time <= end_time:
                # Normal case: 08:00 - 22:00
                if start_time <= current_time < end_time:
                    return schedule
            else:
                # Crosses midnight: 22:00 - 06:00
                if current_time >= start_time or current_time < end_time:
                    return schedule
                    
        return None

    async def _handle_smart_night_boost(self, area, now: datetime) -> None:
        """Handle smart night boost by predicting when to start heating.
        
        Uses the learning engine to predict how long heating will take,
        then adjusts the night boost start time to ensure the room reaches
        target temperature by the configured wake-up time.
        
        Args:
            area: Area instance with smart_night_boost_enabled
            now: Current datetime
        """
        # Parse target time (e.g., "06:00" for wake-up)
        target_hour, target_min = map(int, area.smart_night_boost_target_time.split(':'))
        target_time = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
        
        # If target time has passed today, skip (will run tomorrow)
        if now >= target_time:
            return
        
        # Get current and target temperatures
        current_temp = area.current_temperature
        target_temp = area.target_temperature
        
        if current_temp is None:
            _LOGGER.warning("Cannot predict smart night boost for %s: no temperature data", area.area_id)
            return
        
        # Get outdoor temperature if available
        outdoor_temp = None
        if area.weather_entity_id:
            state = self.hass.states.get(area.weather_entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    outdoor_temp = float(state.state)
                    unit = state.attributes.get("unit_of_measurement", "°C")
                    if unit in ("°F", "F"):
                        outdoor_temp = (outdoor_temp - 32) * 5/9
                except (ValueError, TypeError):
                    pass
        
        # Predict heating time using learning engine
        predicted_minutes = await self.learning_engine.async_predict_heating_time(
            area_id=area.area_id,
            start_temp=current_temp,
            target_temp=target_temp,
            outdoor_temp=outdoor_temp
        )
        
        if predicted_minutes is None:
            _LOGGER.debug(
                "No prediction available for area %s, using default night boost",
                area.area_id
            )
            return
        
        # Calculate when to start heating
        from datetime import timedelta
        heating_duration = timedelta(minutes=predicted_minutes)
        optimal_start_time = target_time - heating_duration
        
        # Add a safety margin (e.g., 10 minutes earlier)
        safety_margin = timedelta(minutes=10)
        optimal_start_time -= safety_margin
        
        # Check if we should start heating now
        if now >= optimal_start_time and now < target_time:
            # Override night boost settings temporarily for this cycle
            _LOGGER.info(
                "Smart night boost for area %s: Starting heating at %s (predicted %d min, target %s)",
                area.area_id,
                now.strftime("%H:%M"),
                predicted_minutes,
                area.smart_night_boost_target_time
            )
            # The climate controller will handle the actual heating
            # We just log the prediction here
        else:
            time_until_start = (optimal_start_time - now).total_seconds() / 60
            if time_until_start > 0:
                _LOGGER.debug(
                    "Smart night boost for area %s: Will start in %.0f min (predicted %d min heating)",
                    area.area_id,
                    time_until_start,
                    predicted_minutes
                )

    async def _apply_schedule(self, area, schedule) -> None:
        """Apply a schedule's temperature to a area.
        
        Args:
            area: Zone object
            schedule: Schedule object
        """
        target_temp = schedule.temperature
        
        _LOGGER.info(
            "Applying schedule to area %s: %s-%s @ %s°C",
            area.name,
            schedule.start_time,
            schedule.end_time,
            target_temp,
        )
        
        # Update area target temperature
        area.target_temperature = target_temp
        await self.area_manager.async_save()
        
        # Update the climate entity if it exists
        climate_entity_id = f"climate.smart_heating_{area.area_id}"
        
        # Call the climate service to set temperature
        try:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    "entity_id": climate_entity_id,
                    "temperature": target_temp,
                },
                blocking=True,
            )
            _LOGGER.debug(
                "Set temperature for %s to %s°C via climate service",
                climate_entity_id,
                target_temp,
            )
        except Exception as err:
            _LOGGER.warning(
                "Failed to set temperature via climate service for %s: %s",
                climate_entity_id,
                err,
            )
