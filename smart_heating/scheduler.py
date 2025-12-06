"""Schedule executor for Zone Heater Manager."""
import logging
from datetime import datetime, time
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util
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

    def clear_schedule_cache(self, area_id: str) -> None:
        """Clear the last applied schedule cache for an area.
        
        This should be called when a schedule is removed or modified
        to ensure the scheduler re-evaluates and applies the current schedule.
        
        Args:
            area_id: Area identifier
        """
        if area_id in self._last_applied_schedule:
            del self._last_applied_schedule[area_id]
            _LOGGER.debug("Cleared schedule cache for area %s", area_id)

    async def _async_check_schedules(self, now: Optional[datetime] = None) -> None:
        """Check all area schedules and apply temperatures if needed.
        
        Also handles smart night boost by predicting heating start times.
        
        Args:
            now: Current datetime (for testing, otherwise uses current time)
        """
        # Get current UTC time and convert to HA's configured timezone
        if now is None:
            now = dt_util.utcnow()
        
        # Always convert to HA's configured timezone
        if self.hass.config.time_zone:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(self.hass.config.time_zone)
            now = now.astimezone(tz)
        
        _LOGGER.warning(
            "⏰ Local time = %s (timezone: %s, UTC offset: %s, HA tz: %s)",
            now, now.tzinfo, now.strftime("%z"), self.hass.config.time_zone
        )
            
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
            
            _LOGGER.warning(
                "🔍 SCHEDULE CHECK: %s - %s at %s has %d schedules",
                area.name,
                current_day,
                current_time.strftime("%H:%M"),
                len(area.schedules)
            )
            
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
        
        Handles schedules that cross midnight (e.g., Saturday 22:00 - Sunday 07:00).
        Priority: midnight-crossing schedules checked first as they take precedence.
        
        Args:
            schedules: List of schedule entries
            current_day: Current day name (e.g., "Monday")
            current_time: Current time
            
        Returns:
            Active schedule entry or None
        """
        # Get previous day name for cross-midnight check
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_day_idx = day_order.index(current_day)
        previous_day = day_order[(current_day_idx - 1) % 7]
        
        _LOGGER.warning(
            "🔍 Schedule matching: day=%s, time=%s, previous_day=%s, num_schedules=%d",
            current_day, current_time, previous_day, len(schedules)
        )
        
        # FIRST: Check if a schedule from the previous day extends into today (higher priority)
        for schedule in schedules.values():
            if schedule.day == previous_day:
                start_time = time.fromisoformat(schedule.start_time)
                end_time = time.fromisoformat(schedule.end_time)
                
                # Only check if schedule crosses midnight
                if start_time > end_time:
                    # Check if we're in the early period (< end_time)
                    if current_time < end_time:
                        _LOGGER.warning(
                            "🎯 Matched midnight-crossing schedule from %s: %s-%s (current: %s)",
                            previous_day, schedule.start_time, schedule.end_time, current_time
                        )
                        return schedule
        
        # SECOND: Check midnight-crossing schedules that start today (high priority)
        for schedule in schedules.values():
            if schedule.day == current_day:
                start_time = time.fromisoformat(schedule.start_time)
                end_time = time.fromisoformat(schedule.end_time)
                
                # Crosses midnight: 22:00 - 06:00
                if start_time > end_time:
                    # Only match if we're in the late period (>= start_time)
                    if current_time >= start_time:
                        _LOGGER.warning(
                            "🎯 Matched midnight-crossing schedule: %s %s-%s @ %s (current: %s)",
                            schedule.day, schedule.start_time, schedule.end_time, 
                            getattr(schedule, 'preset_mode', getattr(schedule, 'temperature', '?')),
                            current_time
                        )
                        return schedule
        
        # THIRD: Check normal (non-midnight-crossing) schedules for current day
        for schedule in schedules.values():
            if schedule.day == current_day:
                start_time = time.fromisoformat(schedule.start_time)
                end_time = time.fromisoformat(schedule.end_time)
                
                # Normal case: 08:00 - 22:00
                if start_time <= end_time:
                    if start_time <= current_time < end_time:
                        _LOGGER.warning(
                            "🎯 Matched normal schedule: %s %s-%s @ %s (current: %s)",
                            schedule.day, schedule.start_time, schedule.end_time,
                            getattr(schedule, 'preset_mode', getattr(schedule, 'temperature', '?')),
                            current_time
                        )
                        return schedule
        
        _LOGGER.warning(
            "❌ No schedule matched for %s at %s",
            current_day, current_time
        )
        return None

    async def _handle_smart_night_boost(self, area, now: datetime) -> None:
        """Handle smart night boost by predicting when to start heating.
        
        Uses the learning engine to predict how long heating will take,
        then adjusts the night boost start time to ensure the room reaches
        target temperature by the configured wake-up time OR the first morning schedule.
        
        Args:
            area: Area instance with smart_night_boost_enabled
            now: Current datetime
        """
        # Determine target time: either configured target OR first morning schedule
        target_time = None
        target_temp = area.target_temperature
        
        # First, check if there's a morning schedule that should be our target
        morning_schedule = self._find_first_morning_schedule(area.schedules, now)
        
        if morning_schedule:
            # Use schedule's start time as target
            target_hour, target_min = map(int, morning_schedule.start_time.split(':'))
            target_time = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
            
            # Determine target temperature from schedule
            if morning_schedule.preset_mode:
                # Get temperature from preset mode
                target_temp = self._get_preset_temperature(area, morning_schedule.preset_mode)
            elif morning_schedule.temperature is not None:
                target_temp = morning_schedule.temperature
            
            _LOGGER.debug(
                "Smart night boost for %s: Using morning schedule at %s (target temp: %.1f°C)",
                area.area_id,
                morning_schedule.start_time,
                target_temp
            )
            if hasattr(self, 'area_logger') and self.area_logger:
                self.area_logger.log_event(
                    area.area_id,
                    "smart_boost",
                    f"Smart night boost: targeting morning schedule at {morning_schedule.start_time}",
                    {
                        "target_time": morning_schedule.start_time,
                        "target_temp": target_temp,
                        "preset_mode": morning_schedule.preset_mode
                    }
                )
        elif area.smart_night_boost_target_time:
            # Fallback to configured target time
            target_hour, target_min = map(int, area.smart_night_boost_target_time.split(':'))
            target_time = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
            _LOGGER.debug(
                "Smart night boost for %s: Using configured target time %s",
                area.area_id,
                area.smart_night_boost_target_time
            )
        else:
            # No target configured and no morning schedule
            return
        
        # If target time has passed today, use tomorrow's target
        if now >= target_time:
            target_time += timedelta(days=1)
        
        # Get current temperature
        current_temp = area.current_temperature
        
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
            current_temp=current_temp,
            target_temp=target_temp
        )
        
        if predicted_minutes is None:
            _LOGGER.debug(
                "No prediction available for area %s, using default night boost",
                area.area_id
            )
            return
        
        # Calculate when to start heating
        heating_duration = timedelta(minutes=predicted_minutes)
        optimal_start_time = target_time - heating_duration
        
        # Add a safety margin (e.g., 10 minutes earlier)
        safety_margin = timedelta(minutes=10)
        optimal_start_time -= safety_margin
        
        # Check if we should start heating now
        if now >= optimal_start_time and now < target_time:
            # Override night boost settings temporarily for this cycle
            _LOGGER.info(
                "Smart night boost for area %s: Starting heating at %s (predicted %d min, target %s @ %.1f°C)",
                area.area_id,
                now.strftime("%H:%M"),
                predicted_minutes,
                target_time.strftime("%H:%M"),
                target_temp
            )
            if hasattr(self, 'area_logger') and self.area_logger:
                self.area_logger.log_event(
                    area.area_id,
                    "smart_boost",
                    f"Smart night boost activated - predicted {predicted_minutes} min to reach {target_temp:.1f}°C",
                    {
                        "predicted_minutes": predicted_minutes,
                        "target_time": target_time.strftime("%H:%M"),
                        "target_temp": target_temp,
                        "start_time": now.strftime("%H:%M")
                    }
                )
            # The climate controller will handle the actual heating
            # We just log the prediction here
        else:
            time_until_start = (optimal_start_time - now).total_seconds() / 60
            if time_until_start > 0:
                _LOGGER.debug(
                    "Smart night boost for area %s: Will start in %.0f min (predicted %d min heating to %.1f°C)",
                    area.area_id,
                    time_until_start,
                    predicted_minutes,
                    target_temp
                )
    
    def _find_first_morning_schedule(self, schedules: dict, now: datetime) -> Optional[object]:
        """Find the first schedule entry in the morning (after midnight, before noon).
        
        This is used by smart night boost to determine when to start heating.
        
        Args:
            schedules: Dictionary of schedule entries
            now: Current datetime
            
        Returns:
            First morning schedule or None
        """
        current_day = DAYS_OF_WEEK[now.weekday()]
        morning_schedules = []
        
        for schedule in schedules.values():
            if not schedule.enabled:
                continue
            
            # Check if schedule is for current day
            if schedule.day != current_day:
                continue
            
            # Parse start time
            try:
                start_hour, start_min = map(int, schedule.start_time.split(':'))
                
                # Consider "morning" as 00:00 to 12:00
                if 0 <= start_hour < 12:
                    morning_schedules.append((start_hour, start_min, schedule))
            except (ValueError, AttributeError):
                continue
        
        # Sort by time and return earliest
        if morning_schedules:
            morning_schedules.sort(key=lambda x: (x[0], x[1]))
            return morning_schedules[0][2]  # Return schedule object
        
        return None
    
    def _get_preset_temperature(self, area, preset_mode: str) -> float:
        """Get the effective temperature for a preset mode.
        
        Args:
            area: Area instance
            preset_mode: Preset mode name (away, eco, comfort, home, sleep, activity)
            
        Returns:
            Temperature for the preset
        """
        preset_temps = {
            "away": (area.away_temp, area.use_global_away),
            "eco": (area.eco_temp, area.use_global_eco),
            "comfort": (area.comfort_temp, area.use_global_comfort),
            "home": (area.home_temp, area.use_global_home),
            "sleep": (area.sleep_temp, area.use_global_sleep),
            "activity": (area.activity_temp, area.use_global_activity),
        }
        
        if preset_mode in preset_temps:
            temp, use_global = preset_temps[preset_mode]
            # If using global, get from area_manager's global presets
            if use_global and hasattr(self.area_manager, f'global_{preset_mode}_temp'):
                return getattr(self.area_manager, f'global_{preset_mode}_temp')
            return temp
        
        # Default fallback
        return area.target_temperature

    async def _apply_schedule(self, area, schedule) -> None:
        """Apply a schedule's temperature or preset mode to an area.
        
        Args:
            area: Zone object
            schedule: Schedule object
        """
        climate_entity_id = f"climate.smart_heating_{area.area_id}"
        
        # Apply preset mode if specified
        if schedule.preset_mode:
            _LOGGER.info(
                "Applying schedule to area %s: %s-%s @ preset '%s'",
                area.name,
                schedule.start_time,
                schedule.end_time,
                schedule.preset_mode,
            )
            if hasattr(self, 'area_logger') and self.area_logger:
                preset_temp = self._get_preset_temperature(area, schedule.preset_mode)
                self.area_logger.log_event(
                    area.area_id,
                    "schedule",
                    f"Schedule activated: {schedule.start_time}-{schedule.end_time} @ preset '{schedule.preset_mode}' ({preset_temp:.1f}°C)",
                    {
                        "schedule_id": schedule.schedule_id,
                        "start_time": schedule.start_time,
                        "end_time": schedule.end_time,
                        "preset_mode": schedule.preset_mode,
                        "preset_temp": preset_temp
                    }
                )
            
            # Set preset mode
            area.preset_mode = schedule.preset_mode
            
            # Clear manual override when schedule applies a preset
            if hasattr(area, 'manual_override') and area.manual_override:
                _LOGGER.info(
                    "Clearing manual override for %s - schedule now controls preset",
                    area.name
                )
                area.manual_override = False
            
            await self.area_manager.async_save()
            
            _LOGGER.debug(
                "Set preset mode for area %s to %s",
                area.area_id,
                schedule.preset_mode,
            )
        else:
            # Apply temperature directly
            target_temp = schedule.temperature
            
            _LOGGER.info(
                "Applying schedule to area %s: %s-%s @ %s°C",
                area.name,
                schedule.start_time,
                schedule.end_time,
                target_temp,
            )
            if hasattr(self, 'area_logger') and self.area_logger:
                self.area_logger.log_event(
                    area.area_id,
                    "schedule",
                    f"Schedule activated: {schedule.start_time}-{schedule.end_time} @ {target_temp}°C",
                    {
                        "schedule_id": schedule.schedule_id,
                        "start_time": schedule.start_time,
                        "end_time": schedule.end_time,
                        "temperature": target_temp
                    }
                )
            
            # Update area target temperature
            area.target_temperature = target_temp
            
            # Clear manual override when schedule applies a temperature
            if hasattr(area, 'manual_override') and area.manual_override:
                _LOGGER.info(
                    "Clearing manual override for %s - schedule now controls temperature",
                    area.name
                )
                area.manual_override = False
            
            await self.area_manager.async_save()
            
            # Update the climate entity if it exists
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

