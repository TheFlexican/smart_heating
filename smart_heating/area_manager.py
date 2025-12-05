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
        temperature: float,
        days: list[str] | None = None,
        enabled: bool = True,
        day: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> None:
        """Initialize a schedule.
        
        Args:
            schedule_id: Unique identifier
            time: Time in HH:MM format (legacy)
            temperature: Target temperature
            days: Days of week (mon, tue, etc.) or None for all days (legacy)
            enabled: Whether schedule is active
            day: Day name (Monday, Tuesday, etc.) - new format
            start_time: Start time in HH:MM format - new format
            end_time: End time in HH:MM format - new format
        """
        self.schedule_id = schedule_id
        # Support both old and new formats
        self.time = start_time or time
        self.start_time = start_time or time
        self.end_time = end_time or "23:59"  # Default end time
        self.temperature = temperature
        
        # Convert between day formats
        day_map = {
            "Monday": "mon", "Tuesday": "tue", "Wednesday": "wed",
            "Thursday": "thu", "Friday": "fri", "Saturday": "sat", "Sunday": "sun"
        }
        reverse_day_map = {v: k for k, v in day_map.items()}
        
        if day:
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
        
        # Check day of week
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
        return {
            "id": self.schedule_id,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "temperature": self.temperature,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create from dictionary."""
        return cls(
            schedule_id=data["id"],
            time=data.get("time"),
            temperature=data["temperature"],
            days=data.get("days"),
            enabled=data.get("enabled", True),
            day=data.get("day"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
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
        action_when_away: str = "reduce_temperature",
        action_when_home: str = "increase_temperature",
        temp_drop_when_away: float | None = None,
        temp_boost_when_home: float | None = None
    ) -> None:
        """Add a presence/motion sensor to the area.
        
        Args:
            entity_id: Entity ID of the presence sensor
            action_when_away: Action when no presence detected
            action_when_home: Action when presence detected
            temp_drop_when_away: Temperature drop when away
            temp_boost_when_home: Temperature boost when home
        """
        # Check if sensor already exists
        existing = [s for s in self.presence_sensors if s.get("entity_id") == entity_id]
        if existing:
            _LOGGER.warning("Presence sensor %s already exists in area %s", entity_id, self.area_id)
            return
            
        sensor_config = {
            "entity_id": entity_id,
            "action_when_away": action_when_away,
            "action_when_home": action_when_home,
        }
        if action_when_away == "reduce_temperature":
            sensor_config["temp_drop_when_away"] = temp_drop_when_away if temp_drop_when_away is not None else 3.0
        if action_when_home == "increase_temperature":
            sensor_config["temp_boost_when_home"] = temp_boost_when_home if temp_boost_when_home is not None else DEFAULT_PRESENCE_TEMP_BOOST
            
        self.presence_sensors.append(sensor_config)
        _LOGGER.debug("Added presence sensor %s to area %s", entity_id, self.area_id)

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
        preset_temps = {
            PRESET_AWAY: self.away_temp,
            PRESET_ECO: self.eco_temp,
            PRESET_COMFORT: self.comfort_temp,
            PRESET_HOME: self.home_temp,
            PRESET_SLEEP: self.sleep_temp,
            PRESET_ACTIVITY: self.activity_temp,
            PRESET_BOOST: self.boost_temp,
        }
        return preset_temps.get(self.preset_mode, self.target_temperature)

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode for the area.
        
        Args:
            preset_mode: Preset mode (away, eco, comfort, etc.)
        """
        old_mode = self.preset_mode
        self.preset_mode = preset_mode
        _LOGGER.debug("Set preset mode for area %s from %s to %s", self.area_id, old_mode, preset_mode)

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
        else:
            # Priority 4: Schedule temperature (if available)
            target = self.get_active_schedule_temperature(current_time)
            if target is None:
                # Priority 5: Base target temperature
                target = self.target_temperature
        
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
            
            if is_active:
                target += self.night_boost_offset
                _LOGGER.debug(
                    "Night boost active for area %s (%s-%s): %.1f°C + %.1f°C = %.1f°C",
                    self.area_id, self.night_boost_start_time, self.night_boost_end_time,
                    target - self.night_boost_offset, self.night_boost_offset, target
                )
        
        # Priority 7: Presence sensor actions
        if len(self.presence_sensors) > 0:
            for sensor in self.presence_sensors:
                # Check if presence is detected (this will be updated by climate_controller)
                if self.presence_detected:
                    action = sensor.get("action_when_home", "increase_temperature")
                    if action == "set_comfort":
                        target = self.comfort_temp
                    elif action == "increase_temperature":
                        temp_boost = sensor.get("temp_boost_when_home", DEFAULT_PRESENCE_TEMP_BOOST)
                        target += temp_boost
                        _LOGGER.debug(
                            "Presence detected in area %s: adding %.1f°C boost (final: %.1f°C)",
                            self.area_id, temp_boost, target
                        )
                else:
                    # No presence detected (away)
                    action = sensor.get("action_when_away", "reduce_temperature")
                    if action == "turn_off":
                        return 5.0  # Turn off heating (frost protection)
                    elif action == "set_eco":
                        target = self.eco_temp
                    elif action == "reduce_temperature":
                        temp_drop = sensor.get("temp_drop_when_away", 3.0)
                        target -= temp_drop
                        _LOGGER.debug(
                            "No presence in area %s: reducing %.1f°C (final: %.1f°C)",
                            self.area_id, temp_drop, target
                        )
        
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
            
            # Load areas
            if "areas" in data:
                for area_data in data["areas"]:
                    area = Area.from_dict(area_data)
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
        
        area.target_temperature = temperature
        _LOGGER.info("Set area %s target temperature to %.1f°C", area_id, temperature)

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
