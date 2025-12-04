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

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager) -> None:
        """Initialize the schedule executor.
        
        Args:
            hass: Home Assistant instance
            area_manager: Zone manager instance
        """
        self.hass = hass
        self.area_manager = area_manager
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
