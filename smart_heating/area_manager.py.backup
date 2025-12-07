"""Zone Manager for Smart Heating integration."""
import logging
from typing import Any
from datetime import datetime, time, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_DEVICES,
    ATTR_ENABLED,
    ATTR_TARGET_TEMPERATURE,
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    ATTR_OPENTHERM_GATEWAY,
    ATTR_OPENTHERM_ENABLED,
    ATTR_TRV_HEATING_TEMP,
    ATTR_TRV_IDLE_TEMP,
    ATTR_TRV_TEMP_OFFSET,
    ATTR_HYSTERESIS,
    ATTR_NIGHT_BOOST_ENABLED,
    ATTR_NIGHT_BOOST_OFFSET,
    ATTR_NIGHT_BOOST_START_TIME,
    ATTR_NIGHT_BOOST_END_TIME,
    DEFAULT_NIGHT_BOOST_START_TIME,
    DEFAULT_NIGHT_BOOST_END_TIME,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    DEVICE_TYPE_SWITCH,
    DEVICE_TYPE_WINDOW_SENSOR,
    DEVICE_TYPE_PRESENCE_SENSOR,
    STATE_HEATING,
    STATE_IDLE,
    STATE_OFF,
    STORAGE_KEY,
    STORAGE_VERSION,
    DEFAULT_TRV_HEATING_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    DEFAULT_TRV_TEMP_OFFSET,
    PRESET_NONE,
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_COMFORT,
    PRESET_HOME,
    PRESET_SLEEP,
    PRESET_ACTIVITY,
    PRESET_BOOST,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_OFF,
    DEFAULT_AWAY_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_SLEEP_TEMP,
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_WINDOW_OPEN_TEMP_DROP,
    DEFAULT_PRESENCE_TEMP_BOOST,
    DEFAULT_FROST_PROTECTION_TEMP,
)

_LOGGER = logging.getLogger(__name__)


class Schedule:
    """Representation of a temperature schedule."""

    def __init__(
        self,
        schedule_id: str,
        time: str,
        temperature: float = None,
        days: list[str] | None = None,
        enabled: bool = True,
        day: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        preset_mode: str | None = None,
        date: str | None = None,
    ) -> None:
        """Initialize a schedule.
        
        Args:
            schedule_id: Unique identifier
            time: Time in HH:MM format (legacy)
            temperature: Target temperature (optional if preset_mode is used)
            days: Days of week (mon, tue, etc.) or None for all days (legacy)
            enabled: Whether schedule is active
            day: Day name (Monday, Tuesday, etc.) - new format (single day, legacy)
            start_time: Start time in HH:MM format - new format
            end_time: End time in HH:MM format - new format
            preset_mode: Preset mode name (away, eco, comfort, home, sleep, activity)
            date: Specific date for one-time schedules (YYYY-MM-DD format)
        """
        self.schedule_id = schedule_id
        # Support both old and new formats
        self.time = start_time or time
        self.start_time = start_time or time
        self.end_time = end_time or "23:59"  # Default end time
        self.temperature = temperature
        self.preset_mode = preset_mode
        self.date = date  # Specific date for one-time schedules
        
        # Convert between day formats
        day_map = {
            "Monday": "mon", "Tuesday": "tue", "Wednesday": "wed",
            "Thursday": "thu", "Friday": "fri", "Saturday": "sat", "Sunday": "sun"
        }
        reverse_day_map = {v: k for k, v in day_map.items()}
        
        # If date is specified, this is a date-specific schedule (not recurring weekly)
        if date:
            self.day = None
            self.days = None
        elif day:
            self.day = day
            self.days = [day_map.get(day, "mon")]
        elif days:
            self.days = days
            # Use first day for display
            self.day = reverse_day_map.get(days[0], "Monday") if days else "Monday"
        else:
            self.days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
            self.day = "Monday"
        
        self.enabled = enabled

    def is_active(self, current_time: datetime) -> bool:
        """Check if schedule is active at given time.
        
        Args:
            current_time: Current datetime
            
        Returns:
            True if schedule should be active
        """
        if not self.enabled:
            return False
        
        # Check if this is a date-specific schedule
        if self.date:
            current_date_str = current_time.strftime("%Y-%m-%d")
            if current_date_str != self.date:
                return False
            # Date matches, check time range
            schedule_start = datetime.strptime(self.start_time, "%H:%M").time()
            schedule_end = datetime.strptime(self.end_time, "%H:%M").time()
            current_time_only = current_time.time()
            return schedule_start <= current_time_only < schedule_end
        
        # Otherwise, check day of week for recurring schedules
        if not self.days:
            return False
            
        day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        current_day = day_names[current_time.weekday()]
        if current_day not in self.days:
            return False
        
        # Check time (within 30 minutes)
        schedule_time = datetime.strptime(self.time, "%H:%M").time()
        current_time_only = current_time.time()
        
        # Simple time comparison - schedule is active from its time until next schedule
        return current_time_only >= schedule_time
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.schedule_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "enabled": self.enabled,
        }
        
        # Add date for date-specific schedules
        if self.date:
            result["date"] = self.date
        # Add days for recurring weekly schedules
        elif self.days:
            # Convert internal format to frontend format
            day_map = {
                "mon": "Monday", "tue": "Tuesday", "wed": "Wednesday",
                "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday"
            }
            result["days"] = [day_map.get(d, d) for d in self.days]
            # Keep single day for backwards compatibility
            if self.day:
                result["day"] = self.day
        
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.preset_mode is not None:
            result["preset_mode"] = self.preset_mode
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        # Convert frontend days format to internal format if needed
        days_data = data.get("days")
        if days_data and isinstance(days_data, list) and days_data:
            # Check if it's frontend format (Monday, Tuesday, etc.)
            day_map = {
                "Monday": "mon", "Tuesday": "tue", "Wednesday": "wed",
                "Thursday": "thu", "Friday": "fri", "Saturday": "sat", "Sunday": "sun"
            }
            if days_data[0] in day_map:
                days_data = [day_map.get(d, d) for d in days_data]
        
        return cls(
            schedule_id=data["id"],
            time=data.get("time"),
            temperature=data.get("temperature"),
            days=days_data,
            enabled=data.get("enabled", True),
            day=data.get("day"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            preset_mode=data.get("preset_mode"),
            date=data.get("date"),
        )



class Area:
    """Representation of a heating area."""

    def __init__(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
    ) -> None:
        """Initialize a area.
        
        Args:
            area_id: Unique identifier for the area
            name: Display name of the area
            target_temperature: Target temperature for the area
            enabled: Whether the area is enabled
        """
        self.area_id = area_id
        self.name = name
        self.target_temperature = target_temperature
        self.enabled = enabled
        self.devices: dict[str, dict[str, Any]] = {}
        self.schedules: dict[str, Schedule] = {}
        self._current_temperature: float | None = None
        self.hidden: bool = False  # Whether area is hidden from main view
        self.area_manager: "AreaManager | None" = None  # Reference to parent AreaManager
        
        # Night boost settings
        self.night_boost_enabled: bool = True
        self.night_boost_offset: float = 0.5  # Add 0.5°C during night hours
        self.night_boost_start_time: str = DEFAULT_NIGHT_BOOST_START_TIME
        self.night_boost_end_time: str = DEFAULT_NIGHT_BOOST_END_TIME
        
        # Smart night boost settings
        self.smart_night_boost_enabled: bool = False
        self.smart_night_boost_target_time: str = "06:00"  # Time when room should be at target temp
        self.weather_entity_id: str | None = None  # Outdoor temperature sensor
        
        # Preset mode settings
        self.preset_mode: str = PRESET_NONE
        self.away_temp: float = DEFAULT_AWAY_TEMP
        self.eco_temp: float = DEFAULT_ECO_TEMP
        self.comfort_temp: float = DEFAULT_COMFORT_TEMP
        self.home_temp: float = DEFAULT_HOME_TEMP
        self.sleep_temp: float = DEFAULT_SLEEP_TEMP
        self.activity_temp: float = DEFAULT_ACTIVITY_TEMP
        
        # Preset configuration - choose between global or custom temperatures
        self.use_global_away: bool = True
        self.use_global_eco: bool = True
        self.use_global_comfort: bool = True
        self.use_global_home: bool = True
        self.use_global_sleep: bool = True
        self.use_global_activity: bool = True
        
        # Boost mode settings
        self.boost_mode_active: bool = False
        self.boost_duration: int = 60  # minutes
        self.boost_temp: float = 25.0
        self.boost_end_time: datetime | None = None
        
        # HVAC mode (heat/cool/auto)
        self.hvac_mode: str = HVAC_MODE_HEAT
        
        # Window sensor settings (new config structure)
        self.window_sensors: list[dict[str, Any]] = []  # List of window sensor configs
        self.window_is_open: bool = False  # Cached state
        
        # Presence sensor settings (new config structure)
        self.presence_sensors: list[dict[str, Any]] = []  # List of presence sensor configs
        self.presence_detected: bool = False  # Cached state
        self.use_global_presence: bool = False  # Use global presence sensors instead of area-specific
        
        # Manual override mode - when user manually adjusts thermostat outside the app
        self.manual_override: bool = False  # True when thermostat was manually adjusted
        
        # Switch/pump control setting
        self.shutdown_switches_when_idle: bool = True  # Turn off switches/pumps when area not heating
        
        # Hysteresis override - None means use global setting
        self.hysteresis_override: float | None = None  # Area-specific hysteresis in °C (0.1-2.0)

    def add_device(self, device_id: str, device_type: str, mqtt_topic: str | None = None) -> None:
        """Add a device to the area.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of device (thermostat, temperature_sensor, etc.)
            mqtt_topic: MQTT topic for the device (optional)
        """
        self.devices[device_id] = {
            "type": device_type,
            "mqtt_topic": mqtt_topic,
            "entity_id": None,
        }
        _LOGGER.debug("Added device %s (type: %s) to area %s", device_id, device_type, self.area_id)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the area.
        
        Args:
            device_id: Unique identifier for the device
        """
        if device_id in self.devices:
            del self.devices[device_id]
            _LOGGER.debug("Removed device %s from area %s", device_id, self.area_id)

    def get_temperature_sensors(self) -> list[str]:
        """Get all temperature sensor device IDs in the area.
        
        Returns:
            List of temperature sensor device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_TEMPERATURE_SENSOR
        ]

    def get_thermostats(self) -> list[str]:
        """Get all thermostat device IDs in the area.
        
        Returns:
            List of thermostat device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_THERMOSTAT
        ]

    def get_opentherm_gateways(self) -> list[str]:
        """Get all OpenTherm gateway device IDs in the area.
        
        Returns:
            List of OpenTherm gateway device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_OPENTHERM_GATEWAY
        ]

    def get_switches(self) -> list[str]:
        """Get all switch device IDs in the area (pumps, relays, etc.).
        
        Returns:
            List of switch device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_SWITCH
        ]

    def get_valves(self) -> list[str]:
        """Get all valve device IDs in the area (TRVs, motorized valves).
        
        Returns:
            List of valve device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_VALVE
        ]

    def add_window_sensor(
        self, 
        entity_id: str, 
        action_when_open: str = "reduce_temperature",
        temp_drop: float | None = None
    ) -> None:
        """Add a window/door sensor to the area.
        
        Args:
            entity_id: Entity ID of the window/door sensor
            action_when_open: Action to take when window opens (turn_off, reduce_temperature, none)
            temp_drop: Temperature drop when open (only for reduce_temperature action)
        """
        # Check if sensor already exists
        existing = [s for s in self.window_sensors if s.get("entity_id") == entity_id]
        if existing:
            _LOGGER.warning("Window sensor %s already exists in area %s", entity_id, self.area_id)
            return
            
        sensor_config = {
            "entity_id": entity_id,
            "action_when_open": action_when_open,
        }
        if action_when_open == "reduce_temperature":
            sensor_config["temp_drop"] = temp_drop if temp_drop is not None else DEFAULT_WINDOW_OPEN_TEMP_DROP
            
        self.window_sensors.append(sensor_config)
        _LOGGER.debug("Added window sensor %s to area %s with action %s", entity_id, self.area_id, action_when_open)

    def remove_window_sensor(self, entity_id: str) -> None:
        """Remove a window/door sensor from the area.
        
        Args:
            entity_id: Entity ID of the window/door sensor
        """
        self.window_sensors = [s for s in self.window_sensors if s.get("entity_id") != entity_id]
        _LOGGER.debug("Removed window sensor %s from area %s", entity_id, self.area_id)

    def add_presence_sensor(
        self,
        entity_id: str,
    ) -> None:
        """Add a presence/motion sensor to the area.
        
        Presence sensors control preset mode switching:
        - When away: Switch to "away" preset
        - When home: Switch back to previous preset (typically "home")
        
        Args:
            entity_id: Entity ID of the presence sensor (person.* or binary_sensor.*)
        """
        # Check if sensor already exists
        existing = [s for s in self.presence_sensors if s.get("entity_id") == entity_id]
        if existing:
            _LOGGER.warning("Presence sensor %s already exists in area %s", entity_id, self.area_id)
            return
            
        sensor_config = {
            "entity_id": entity_id,
        }
            
        self.presence_sensors.append(sensor_config)
        _LOGGER.debug("Added presence sensor %s to area %s (controls preset mode)", entity_id, self.area_id)

    def remove_presence_sensor(self, entity_id: str) -> None:
        """Remove a presence/motion sensor from the area.
        
        Args:
            entity_id: Entity ID of the presence sensor
        """
        self.presence_sensors = [s for s in self.presence_sensors if s.get("entity_id") != entity_id]
        _LOGGER.debug("Removed presence sensor %s from area %s", entity_id, self.area_id)

    def get_preset_temperature(self) -> float:
        """Get the target temperature for the current preset mode.
        
        Returns:
            Temperature for current preset mode
        """
        # Determine which temperature to use based on use_global_* flags
        if self.area_manager:
            away_temp = self.area_manager.global_away_temp if self.use_global_away else self.away_temp
            eco_temp = self.area_manager.global_eco_temp if self.use_global_eco else self.eco_temp
            comfort_temp = self.area_manager.global_comfort_temp if self.use_global_comfort else self.comfort_temp
            home_temp = self.area_manager.global_home_temp if self.use_global_home else self.home_temp
            sleep_temp = self.area_manager.global_sleep_temp if self.use_global_sleep else self.sleep_temp
            activity_temp = self.area_manager.global_activity_temp if self.use_global_activity else self.activity_temp
            
            _LOGGER.debug(
                "Area %s: preset=%s, use_global_home=%s, global_home_temp=%.1f°C, area_home_temp=%.1f°C, selected_home_temp=%.1f°C",
                self.area_id, self.preset_mode, self.use_global_home,
                self.area_manager.global_home_temp, self.home_temp, home_temp
            )
        else:
            # Fallback to area-specific temperatures if no area_manager
            _LOGGER.warning("Area %s: No area_manager reference! Using fallback temps", self.area_id)
            away_temp = self.away_temp
            eco_temp = self.eco_temp
            comfort_temp = self.comfort_temp
            home_temp = self.home_temp
            sleep_temp = self.sleep_temp
            activity_temp = self.activity_temp
        
        preset_temps = {
            PRESET_AWAY: away_temp,
            PRESET_ECO: eco_temp,
            PRESET_COMFORT: comfort_temp,
            PRESET_HOME: home_temp,
            PRESET_SLEEP: sleep_temp,
            PRESET_ACTIVITY: activity_temp,
            PRESET_BOOST: self.boost_temp,  # Boost is always area-specific
        }
        result = preset_temps.get(self.preset_mode, self.target_temperature)
        _LOGGER.debug("Area %s: get_preset_temperature() returning %.1f°C", self.area_id, result)
        return result

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for the area.
        
        Args:
            preset_mode: Preset mode (away, eco, comfort, etc.)
        """
        old_mode = self.preset_mode
        old_effective = self.get_effective_target_temperature()
        self.preset_mode = preset_mode
        new_effective = self.get_effective_target_temperature()
        
        _LOGGER.warning(
            "Area %s: Preset mode %s → %s | Effective temp: %.1f°C → %.1f°C (base: %.1f°C)",
            self.area_id, old_mode, preset_mode, old_effective, new_effective, self.target_temperature
        )

    def set_boost_mode(self, duration: int, temp: float | None = None) -> None:
        """Activate boost mode for a specified duration.
        
        Args:
            duration: Duration in minutes
            temp: Optional boost temperature (defaults to self.boost_temp)
        """
        self.boost_mode_active = True
        self.boost_duration = duration
        if temp is not None:
            self.boost_temp = temp
        self.boost_end_time = datetime.now() + timedelta(minutes=duration)
        self.preset_mode = PRESET_BOOST
        _LOGGER.info("Activated boost mode for area %s: %d minutes at %.1f°C", 
                     self.area_id, duration, self.boost_temp)

    def cancel_boost_mode(self) -> None:
        """Cancel active boost mode."""
        if self.boost_mode_active:
            self.boost_mode_active = False
            self.boost_end_time = None
            self.preset_mode = PRESET_NONE
            _LOGGER.info("Cancelled boost mode for area %s", self.area_id)

    def check_boost_expiry(self) -> bool:
        """Check if boost mode has expired and cancel if needed.
        
        Returns:
            True if boost was cancelled, False otherwise
        """
        if self.boost_mode_active and self.boost_end_time:
            if datetime.now() >= self.boost_end_time:
                self.cancel_boost_mode()
                return True
        return False

    def add_schedule(self, schedule: Schedule) -> None:
        """Add a schedule to the area.
        
        Args:
            schedule: Schedule instance
        """
        self.schedules[schedule.schedule_id] = schedule
        _LOGGER.debug("Added schedule %s to area %s", schedule.schedule_id, self.area_id)

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the area.
        
        Args:
            schedule_id: Schedule identifier
        """
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            _LOGGER.debug("Removed schedule %s from area %s", schedule_id, self.area_id)

    def get_active_schedule_temperature(self, current_time: datetime | None = None) -> float | None:
        """Get the temperature from the currently active schedule.
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Temperature from active schedule or None
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Find all active schedules and get the latest one
        active_schedules = [
            s for s in self.schedules.values()
            if s.is_active(current_time)
        ]
        
        if not active_schedules:
            return None
        
        # Sort by time and get the latest
        active_schedules.sort(key=lambda s: s.time, reverse=True)
        return active_schedules[0].temperature

    def get_effective_target_temperature(self, current_time: datetime | None = None) -> float:
        """Get the effective target temperature considering all factors.
        
        Priority order:
        1. Boost mode (if active)
        2. Window open (reduce temperature)
        3. Preset mode temperature
        4. Schedule temperature
        5. Base target temperature
        6. Night boost adjustment
        7. Presence boost (if detected)
        
        Args:
            current_time: Current time (defaults to now)
            
        Returns:
            Effective target temperature
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if boost mode has expired
        self.check_boost_expiry()
        
        # Priority 1: Boost mode
        if self.boost_mode_active:
            return self.boost_temp
        
        # Priority 2: Window open actions
        if self.window_is_open and len(self.window_sensors) > 0:
            # Find sensors with action_when_open configured
            for sensor in self.window_sensors:
                action = sensor.get("action_when_open", "reduce_temperature")
                if action == "turn_off":
                    return 5.0  # Turn off heating (frost protection)
                elif action == "reduce_temperature":
                    temp_drop = sensor.get("temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP)
                    return max(5.0, self.target_temperature - temp_drop)
                # "none" action means no temperature change
        
        # Priority 3: Preset mode temperature
        if self.preset_mode != PRESET_NONE and self.preset_mode != PRESET_BOOST:
            target = self.get_preset_temperature()
            source = f"preset:{self.preset_mode}"
        else:
            # Priority 4: Schedule temperature (if available)
            target = self.get_active_schedule_temperature(current_time)
            if target is None:
                # Priority 5: Base target temperature
                target = self.target_temperature
                source = "base_target"
            else:
                source = "schedule"
        
        # Log what we're starting with for debugging
        _LOGGER.debug(
            "Effective temp calculation for %s: source=%s, target=%.1f°C",
            self.area_id, source, target
        )
        
        # Priority 6: Apply night boost if enabled (additive)
        if self.night_boost_enabled:
            # Parse start and end times
            start_hour, start_min = map(int, self.night_boost_start_time.split(':'))
            end_hour, end_min = map(int, self.night_boost_end_time.split(':'))
            current_hour = current_time.hour
            current_min = current_time.minute
            
            # Check if current time is within night boost period
            # Handle period that crosses midnight
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            current_minutes = current_hour * 60 + current_min
            
            is_active = False
            if start_minutes <= end_minutes:
                # Normal period (e.g., 08:00-18:00)
                is_active = start_minutes <= current_minutes < end_minutes
            else:
                # Period crosses midnight (e.g., 22:00-06:00)
                is_active = current_minutes >= start_minutes or current_minutes < end_minutes
            
            # Important: Only apply night boost if we're NOT in a schedule period
            # This allows schedules (like "sleep" preset from 22:00-06:30) to take precedence
            # Night boost is meant to pre-heat BEFORE the morning schedule starts
            in_schedule = self.get_active_schedule_temperature(current_time) is not None
            
            # Debug logging for troubleshooting
            _LOGGER.debug(
                "Night boost check for %s at %02d:%02d: period=%s-%s, is_active=%s, in_schedule=%s",
                self.area_id, current_hour, current_min,
                self.night_boost_start_time, self.night_boost_end_time,
                is_active, in_schedule
            )
            
            if is_active and not in_schedule:
                old_target = target
                target += self.night_boost_offset
                _LOGGER.debug(
                    "Night boost active for area %s (%s-%s): %.1f°C + %.1f°C = %.1f°C",
                    self.area_id, self.night_boost_start_time, self.night_boost_end_time,
                    old_target, self.night_boost_offset, target
                )
                # Log to area logger if available
                if self.area_manager and hasattr(self.area_manager, 'hass'):
                    area_logger = self.area_manager.hass.data.get("smart_heating", {}).get("area_logger")
                    if area_logger:
                        area_logger.log_event(
                            self.area_id,
                            "temperature",
                            f"Night boost applied: +{self.night_boost_offset}°C",
                            {
                                "base_target": old_target,
                                "boost_offset": self.night_boost_offset,
                                "effective_target": target,
                                "boost_period": f"{self.night_boost_start_time}-{self.night_boost_end_time}",
                                "current_time": f"{current_hour:02d}:{current_min:02d}"
                            }
                        )
        
        # Note: Presence sensor actions are now handled by switching preset modes
        # (see climate_controller.py) rather than adjusting temperature directly
        
        return target

    @property
    def current_temperature(self) -> float | None:
        """Get the current temperature of the area.
        
        Returns:
            Current temperature or None
        """
        return self._current_temperature

    @current_temperature.setter
    def current_temperature(self, value: float | None) -> None:
        """Set the current temperature of the area.
        
        Args:
            value: New temperature value
        """
        self._current_temperature = value

    @property
    def state(self) -> str:
        """Get the current state of the area.
        
        Returns:
            Current state (heating, idle, off)
        """
        if not self.enabled:
            return STATE_OFF
        
        # Check if any thermostat is actively heating
        # This will be updated by the climate controller
        if hasattr(self, '_state'):
            return self._state
        
        # Fallback to temperature-based state
        if self._current_temperature is not None and self.target_temperature is not None:
            if self._current_temperature < self.target_temperature - 0.5:
                return STATE_HEATING
        
        return STATE_IDLE
    
    @state.setter
    def state(self, value: str) -> None:
        """Set the current state of the area.
        
        Args:
            value: New state value
        """
        self._state = value

    def to_dict(self) -> dict[str, Any]:
        """Convert area to dictionary for storage.
        
        Returns:
            Dictionary representation of the area
        """
        return {
            ATTR_AREA_ID: self.area_id,
            ATTR_AREA_NAME: self.name,
            ATTR_TARGET_TEMPERATURE: self.target_temperature,
            ATTR_ENABLED: self.enabled,
            "hidden": self.hidden,
            "manual_override": self.manual_override,
            "shutdown_switches_when_idle": self.shutdown_switches_when_idle,
            ATTR_DEVICES: self.devices,
            "schedules": [s.to_dict() for s in self.schedules.values()],
            "night_boost_enabled": self.night_boost_enabled,
            "night_boost_offset": self.night_boost_offset,
            "night_boost_start_time": self.night_boost_start_time,
            "night_boost_end_time": self.night_boost_end_time,
            "smart_night_boost_enabled": self.smart_night_boost_enabled,
            "smart_night_boost_target_time": self.smart_night_boost_target_time,
            "weather_entity_id": self.weather_entity_id,
            # Preset modes
            "preset_mode": self.preset_mode,
            "away_temp": self.away_temp,
            "eco_temp": self.eco_temp,
            "comfort_temp": self.comfort_temp,
            "home_temp": self.home_temp,
            "sleep_temp": self.sleep_temp,
            "activity_temp": self.activity_temp,
            # Global preset flags
            "use_global_away": self.use_global_away,
            "use_global_eco": self.use_global_eco,
            "use_global_comfort": self.use_global_comfort,
            "use_global_home": self.use_global_home,
            "use_global_sleep": self.use_global_sleep,
            "use_global_activity": self.use_global_activity,
            # Boost mode
            "boost_mode_active": self.boost_mode_active,
            "boost_duration": self.boost_duration,
            "boost_temp": self.boost_temp,
            "boost_end_time": self.boost_end_time.isoformat() if self.boost_end_time else None,
            # HVAC mode
            "hvac_mode": self.hvac_mode,
            # Window sensors (new structure)
            "window_sensors": self.window_sensors,
            # Presence sensors (new structure)
            "presence_sensors": self.presence_sensors,
            "use_global_presence": self.use_global_presence,
            # Hysteresis override
            "hysteresis_override": self.hysteresis_override,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Area":
        """Create a area from dictionary.
        
        Args:
            data: Dictionary with area data
            
        Returns:
            Zone instance
        """
        area = cls(
            area_id=data[ATTR_AREA_ID],
            name=data[ATTR_AREA_NAME],
            target_temperature=data.get(ATTR_TARGET_TEMPERATURE, 20.0),
            enabled=data.get(ATTR_ENABLED, True),
        )
        area.devices = data.get(ATTR_DEVICES, {})
        area.hidden = data.get("hidden", False)
        area.manual_override = data.get("manual_override", False)
        area.shutdown_switches_when_idle = data.get("shutdown_switches_when_idle", True)
        
        # Night boost settings
        area.night_boost_enabled = data.get("night_boost_enabled", True)
        area.night_boost_offset = data.get("night_boost_offset", 0.5)
        area.night_boost_start_time = data.get("night_boost_start_time", DEFAULT_NIGHT_BOOST_START_TIME)
        area.night_boost_end_time = data.get("night_boost_end_time", DEFAULT_NIGHT_BOOST_END_TIME)
        area.smart_night_boost_enabled = data.get("smart_night_boost_enabled", False)
        area.smart_night_boost_target_time = data.get("smart_night_boost_target_time", "06:00")
        area.weather_entity_id = data.get("weather_entity_id")
        
        # Preset modes
        area.preset_mode = data.get("preset_mode", PRESET_NONE)
        area.away_temp = data.get("away_temp", DEFAULT_AWAY_TEMP)
        area.eco_temp = data.get("eco_temp", DEFAULT_ECO_TEMP)
        area.comfort_temp = data.get("comfort_temp", DEFAULT_COMFORT_TEMP)
        area.home_temp = data.get("home_temp", DEFAULT_HOME_TEMP)
        area.sleep_temp = data.get("sleep_temp", DEFAULT_SLEEP_TEMP)
        area.activity_temp = data.get("activity_temp", DEFAULT_ACTIVITY_TEMP)
        
        # Global preset flags (default to True for backward compatibility)
        area.use_global_away = data.get("use_global_away", True)
        area.use_global_eco = data.get("use_global_eco", True)
        area.use_global_comfort = data.get("use_global_comfort", True)
        area.use_global_home = data.get("use_global_home", True)
        area.use_global_sleep = data.get("use_global_sleep", True)
        area.use_global_activity = data.get("use_global_activity", True)
        
        # Boost mode
        area.boost_mode_active = data.get("boost_mode_active", False)
        area.boost_duration = data.get("boost_duration", 60)
        area.boost_temp = data.get("boost_temp", 25.0)
        boost_end_time_str = data.get("boost_end_time")
        if boost_end_time_str:
            from datetime import datetime
            area.boost_end_time = datetime.fromisoformat(boost_end_time_str)
        else:
            area.boost_end_time = None
        
        # HVAC mode
        area.hvac_mode = data.get("hvac_mode", HVAC_MODE_HEAT)
        
        # Hysteresis override
        area.hysteresis_override = data.get("hysteresis_override")
        
        # Window sensors - support both old string format and new dict format
        window_sensors_data = data.get("window_sensors", [])
        if window_sensors_data and isinstance(window_sensors_data[0], str):
            # Legacy format: convert to new format
            area.window_sensors = [
                {
                    "entity_id": entity_id,
                    "action_when_open": "reduce_temperature",
                    "temp_drop": data.get("window_open_temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP)
                }
                for entity_id in window_sensors_data
            ]
        else:
            area.window_sensors = window_sensors_data
        
        # Presence sensors - support both old string format and new dict format
        presence_sensors_data = data.get("presence_sensors", [])
        if presence_sensors_data and isinstance(presence_sensors_data[0], str):
            # Legacy format: convert to new format
            area.presence_sensors = [
                {
                    "entity_id": entity_id,
                    "action_when_away": "reduce_temperature",
                    "action_when_home": "increase_temperature",
                    "temp_drop_when_away": 3.0,
                    "temp_boost_when_home": data.get("presence_temp_boost", DEFAULT_PRESENCE_TEMP_BOOST)
                }
                for entity_id in presence_sensors_data
            ]
        else:
            area.presence_sensors = presence_sensors_data
        
        # Global presence flag (default to False for backward compatibility)
        area.use_global_presence = data.get("use_global_presence", False)
        
        # Load schedules
        for schedule_data in data.get("schedules", []):
            schedule = Schedule.from_dict(schedule_data)
            area.schedules[schedule.schedule_id] = schedule
        
        return area


class AreaManager:
    """Manage heating areas."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the area manager.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.areas: dict[str, Area] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        
        # Global OpenTherm gateway configuration
        self.opentherm_gateway_id: str | None = None
        self.opentherm_enabled: bool = False
        
        # Global TRV configuration
        self.trv_heating_temp: float = DEFAULT_TRV_HEATING_TEMP
        self.trv_idle_temp: float = DEFAULT_TRV_IDLE_TEMP
        self.trv_temp_offset: float = DEFAULT_TRV_TEMP_OFFSET
        
        # Global Frost Protection
        self.frost_protection_enabled: bool = False
        self.frost_protection_temp: float = DEFAULT_FROST_PROTECTION_TEMP
        
        # Global Hysteresis
        self.hysteresis: float = 0.5
        
        # Global Preset Temperatures
        self.global_away_temp: float = DEFAULT_AWAY_TEMP
        self.global_eco_temp: float = DEFAULT_ECO_TEMP
        self.global_comfort_temp: float = DEFAULT_COMFORT_TEMP
        self.global_home_temp: float = DEFAULT_HOME_TEMP
        self.global_sleep_temp: float = DEFAULT_SLEEP_TEMP
        self.global_activity_temp: float = DEFAULT_ACTIVITY_TEMP
        
        # Global Presence Sensors
        self.global_presence_sensors: list[dict] = []
        
        # Safety Sensors (smoke/CO detectors)
        self.safety_sensor_id: str | None = None
        self.safety_sensor_attribute: str = "smoke"  # or "carbon_monoxide", "gas"
        self.safety_sensor_alert_value: str | bool = True  # Value that indicates danger
        self.safety_sensor_enabled: bool = True  # Enabled by default
        self._safety_alert_active: bool = False  # Current alert state
        self._safety_state_unsub = None  # State listener unsubscribe callback
        
        _LOGGER.debug("AreaManager initialized")

    async def async_load(self) -> None:
        """Load areas from storage."""
        _LOGGER.debug("Loading areas from storage")
        data = await self._store.async_load()
        
        if data is not None:
            # Load global configuration
            self.opentherm_gateway_id = data.get("opentherm_gateway_id")
            self.opentherm_enabled = data.get("opentherm_enabled", False)
            self.trv_heating_temp = data.get("trv_heating_temp", DEFAULT_TRV_HEATING_TEMP)
            self.trv_idle_temp = data.get("trv_idle_temp", DEFAULT_TRV_IDLE_TEMP)
            self.trv_temp_offset = data.get("trv_temp_offset", DEFAULT_TRV_TEMP_OFFSET)
            self.frost_protection_enabled = data.get("frost_protection_enabled", False)
            self.frost_protection_temp = data.get("frost_protection_temp", DEFAULT_FROST_PROTECTION_TEMP)
            self.hysteresis = data.get("hysteresis", 0.5)
            
            # Load global preset temperatures
            self.global_away_temp = data.get("global_away_temp", DEFAULT_AWAY_TEMP)
            self.global_eco_temp = data.get("global_eco_temp", DEFAULT_ECO_TEMP)
            self.global_comfort_temp = data.get("global_comfort_temp", DEFAULT_COMFORT_TEMP)
            self.global_home_temp = data.get("global_home_temp", DEFAULT_HOME_TEMP)
            self.global_sleep_temp = data.get("global_sleep_temp", DEFAULT_SLEEP_TEMP)
            self.global_activity_temp = data.get("global_activity_temp", DEFAULT_ACTIVITY_TEMP)
            
            # Load global presence sensors
            self.global_presence_sensors = data.get("global_presence_sensors", [])
            
            # Load safety sensor configuration
            # Support both old single sensor format (backward compatibility) and new multi-sensor format
            if "safety_sensors" in data:
                self.safety_sensors = data.get("safety_sensors", [])
            elif data.get("safety_sensor_id"):
                # Migrate old single sensor format to new list format
                _LOGGER.info("Migrating old safety sensor format to new multi-sensor format")
                self.safety_sensors = [{
                    "sensor_id": data.get("safety_sensor_id"),
                    "attribute": data.get("safety_sensor_attribute", "smoke"),
                    "alert_value": data.get("safety_sensor_alert_value", True),
                    "enabled": data.get("safety_sensor_enabled", True),
                }]
            else:
                self.safety_sensors = []
            self._safety_alert_active = data.get("safety_alert_active", False)
            
            # Load areas
            if "areas" in data:
                for area_data in data["areas"]:
                    area = Area.from_dict(area_data)
                    area.area_manager = self  # Store reference to area_manager
                    self.areas[area.area_id] = area
                _LOGGER.info("Loaded %d areas from storage", len(self.areas))
        else:
            _LOGGER.debug("No areas found in storage")

    async def async_save(self) -> None:
        """Save areas to storage."""
        _LOGGER.debug("Saving areas to storage")
        data = {
            "opentherm_gateway_id": self.opentherm_gateway_id,
            "opentherm_enabled": self.opentherm_enabled,
            "trv_heating_temp": self.trv_heating_temp,
            "trv_idle_temp": self.trv_idle_temp,
            "trv_temp_offset": self.trv_temp_offset,
            "frost_protection_enabled": self.frost_protection_enabled,
            "frost_protection_temp": self.frost_protection_temp,
            "hysteresis": self.hysteresis,
            "global_away_temp": self.global_away_temp,
            "global_eco_temp": self.global_eco_temp,
            "global_comfort_temp": self.global_comfort_temp,
            "global_home_temp": self.global_home_temp,
            "global_sleep_temp": self.global_sleep_temp,
            "global_activity_temp": self.global_activity_temp,
            "global_presence_sensors": self.global_presence_sensors,
            "safety_sensors": self.safety_sensors,
            "safety_alert_active": self._safety_alert_active,
            "areas": [area.to_dict() for area in self.areas.values()]
        }
        await self._store.async_save(data)
        _LOGGER.info("Saved %d areas and global config to storage", len(self.areas))

    def get_area(self, area_id: str) -> Area | None:
        """Get a area by ID.
        
        Args:
            area_id: Zone identifier
            
        Returns:
            Zone or None if not found
        """
        return self.areas.get(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all areas.
        
        Returns:
            Dictionary of all areas
        """
        return self.areas

    def add_device_to_area(
        self,
        area_id: str,
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to a area.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.add_device(device_id, device_type, mqtt_topic)

    def remove_device_from_area(self, area_id: str, device_id: str) -> None:
        """Remove a device from a area.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.remove_device(device_id)

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of a area.
        
        Args:
            area_id: Zone identifier
            temperature: New temperature value
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.current_temperature = temperature
        _LOGGER.debug("Updated area %s temperature to %.1f°C", area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of a area.
        
        Args:
            area_id: Zone identifier
            temperature: Target temperature
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        old_temp = area.target_temperature
        area.target_temperature = temperature
        _LOGGER.warning(
            "TARGET TEMP CHANGE for %s: %.1f°C → %.1f°C (preset: %s)",
            area_id, old_temp, temperature, area.preset_mode
        )

    def enable_area(self, area_id: str) -> None:
        """Enable a area.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.enabled = True
        _LOGGER.info("Enabled area %s", area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable a area.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.enabled = False
        _LOGGER.info("Disabled area %s", area_id)

    def add_schedule_to_area(
        self, 
        area_id: str, 
        schedule_id: str,
        time: str,
        temperature: float,
        days: list[str] | None = None,
    ) -> Schedule:
        """Add a schedule to an area.
        
        Args:
            area_id: Area identifier
            schedule_id: Unique schedule identifier
            time: Time in HH:MM format
            temperature: Target temperature
            days: Days of week or None for all days
            
        Returns:
            Created schedule
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        schedule = Schedule(schedule_id, time, temperature, days)
        area.add_schedule(schedule)
        _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
        return schedule

    def remove_schedule_from_area(self, area_id: str, schedule_id: str) -> None:
        """Remove a schedule from an area.
        
        Args:
            area_id: Area identifier
            schedule_id: Schedule identifier
            
        Raises:
            ValueError: If area does not exist
        """
        area = self.get_area(area_id)
        if area is None:
            raise ValueError(f"Area {area_id} does not exist")
        
        area.remove_schedule(schedule_id)
        _LOGGER.info("Removed schedule %s from area %s", schedule_id, area_id)

    def set_opentherm_gateway(self, gateway_id: str | None, enabled: bool = True) -> None:
        """Set the global OpenTherm gateway.
        
        Args:
            gateway_id: Entity ID of the OpenTherm gateway climate entity (or None to disable)
            enabled: Whether to enable OpenTherm control
        """
        self.opentherm_gateway_id = gateway_id
        self.opentherm_enabled = enabled and gateway_id is not None
        _LOGGER.info("OpenTherm gateway set to %s (enabled: %s)", gateway_id, self.opentherm_enabled)

    def add_safety_sensor(
        self,
        sensor_id: str,
        attribute: str = "smoke",
        alert_value: str | bool = True,
        enabled: bool = True,
    ) -> None:
        """Add a safety sensor (smoke/CO detector).
        
        Args:
            sensor_id: Entity ID of the safety sensor
            attribute: Attribute to monitor (e.g., "smoke", "carbon_monoxide", "gas", "state")
            alert_value: Value that indicates danger (True, "on", "alarm", etc.)
            enabled: Whether safety monitoring is enabled for this sensor
        """
        # Check if sensor already exists
        for sensor in self.safety_sensors:
            if sensor["sensor_id"] == sensor_id:
                # Update existing sensor
                sensor["attribute"] = attribute
                sensor["alert_value"] = alert_value
                sensor["enabled"] = enabled
                _LOGGER.info(
                    "Safety sensor updated: %s (attribute: %s, alert_value: %s, enabled: %s)",
                    sensor_id, attribute, alert_value, enabled
                )
                return
        
        # Add new sensor
        self.safety_sensors.append({
            "sensor_id": sensor_id,
            "attribute": attribute,
            "alert_value": alert_value,
            "enabled": enabled,
        })
        _LOGGER.info(
            "Safety sensor added: %s (attribute: %s, alert_value: %s, enabled: %s)",
            sensor_id, attribute, alert_value, enabled
        )
    
    def remove_safety_sensor(self, sensor_id: str) -> None:
        """Remove a safety sensor by ID.
        
        Args:
            sensor_id: Entity ID of the safety sensor to remove
        """
        self.safety_sensors = [
            s for s in self.safety_sensors if s["sensor_id"] != sensor_id
        ]
        # Clear alert if no sensors remain
        if not self.safety_sensors:
            self._safety_alert_active = False
        _LOGGER.info("Safety sensor removed: %s", sensor_id)
    
    def get_safety_sensors(self) -> list[dict[str, Any]]:
        """Get all configured safety sensors.
        
        Returns:
            List of safety sensor configurations
        """
        return self.safety_sensors.copy()
    
    def check_safety_sensor_status(self) -> tuple[bool, str | None]:
        """Check if any safety sensor is in alert state.
        
        Returns:
            Tuple of (is_alert, sensor_id) - True if any sensor is alerting, with the sensor ID
        """
        if not self.safety_sensors:
            return False, None
        
        for sensor in self.safety_sensors:
            if not sensor.get("enabled", True):
                continue
            
            sensor_id = sensor["sensor_id"]
            attribute = sensor.get("attribute", "smoke")
            alert_value = sensor.get("alert_value", True)
            
            state = self.hass.states.get(sensor_id)
            if not state:
                _LOGGER.warning("Safety sensor %s not found", sensor_id)
                continue
            
            # Check the specified attribute or state
            if attribute == "state":
                # Check state directly
                current_value = state.state
            else:
                # Check attribute
                current_value = state.attributes.get(attribute)
            
            # Compare with alert value
            is_alert = current_value == alert_value
            
            if is_alert:
                _LOGGER.warning(
                    "\ud83d\udea8 Safety sensor %s is in alert state! %s = %s",
                    sensor_id, attribute, current_value
                )
                return True, sensor_id
        
        # No sensors in alert state
        return False, None
        return False
    
    def is_safety_alert_active(self) -> bool:
        """Check if safety alert is currently active.
        
        Returns:
            True if in emergency shutdown mode due to safety alert
        """
        return self._safety_alert_active
    
    def set_safety_alert_active(self, active: bool) -> None:
        """Set the safety alert state.
        
        Args:
            active: Whether safety alert is active
        """
        if self._safety_alert_active != active:
            self._safety_alert_active = active
            _LOGGER.warning("Safety alert state changed to: %s", active)

    def set_trv_temperatures(self, heating_temp: float, idle_temp: float, temp_offset: float | None = None) -> None:
        """Set global TRV temperature limits for areas without position control.
        
        Args:
            heating_temp: Temperature to set when heating (default 25°C)
            idle_temp: Temperature to set when idle (default 10°C)
            temp_offset: Temperature offset above target for temp-controlled valves (default 10°C)
        """
        self.trv_heating_temp = heating_temp
        self.trv_idle_temp = idle_temp
        if temp_offset is not None:
            self.trv_temp_offset = temp_offset
            _LOGGER.info(
                "TRV temperatures set: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
                heating_temp, idle_temp, temp_offset
            )
        else:
            _LOGGER.info("TRV temperatures set: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp)
