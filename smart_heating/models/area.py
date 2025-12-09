"""Area model for Smart Heating integration."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from ..const import (
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    ATTR_DEVICES,
    ATTR_ENABLED,
    ATTR_TARGET_TEMPERATURE,
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_NIGHT_BOOST_END_TIME,
    DEFAULT_NIGHT_BOOST_START_TIME,
    DEFAULT_PRESENCE_TEMP_BOOST,
    DEFAULT_SLEEP_TEMP,
    DEFAULT_WINDOW_OPEN_TEMP_DROP,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_SWITCH,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    HVAC_MODE_HEAT,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
    PRESET_SLEEP,
    STATE_HEATING,
    STATE_IDLE,
    STATE_OFF,
)
from .schedule import Schedule

if TYPE_CHECKING:
    from ..area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


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
        self.area_manager: "AreaManager | None" = (
            None  # Reference to parent AreaManager
        )

        # Night boost settings
        self.night_boost_enabled: bool = True
        self.night_boost_offset: float = 0.5  # Add 0.5°C during night hours
        self.night_boost_start_time: str = DEFAULT_NIGHT_BOOST_START_TIME
        self.night_boost_end_time: str = DEFAULT_NIGHT_BOOST_END_TIME

        # Smart night boost settings
        self.smart_night_boost_enabled: bool = False
        self.smart_night_boost_target_time: str = (
            "06:00"  # Time when room should be at target temp
        )
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
        self.presence_sensors: list[dict[str, Any]] = (
            []
        )  # List of presence sensor configs
        self.presence_detected: bool = False  # Cached state
        self.use_global_presence: bool = (
            False  # Use global presence sensors instead of area-specific
        )

        # Auto preset mode based on presence
        self.auto_preset_enabled: bool = (
            False  # Automatically switch preset based on presence
        )
        self.auto_preset_home: str = PRESET_HOME  # Preset when presence detected
        self.auto_preset_away: str = PRESET_AWAY  # Preset when no presence

        # Manual override mode - when user manually adjusts thermostat outside the app
        self.manual_override: bool = False  # True when thermostat was manually adjusted

        # Switch/pump control setting
        self.shutdown_switches_when_idle: bool = (
            True  # Turn off switches/pumps when area not heating
        )

        # Hysteresis override - None means use global setting
        self.hysteresis_override: float | None = (
            None  # Area-specific hysteresis in °C (0.1-2.0)
        )

        # Primary temperature sensor - which device to use for temperature reading
        self.primary_temperature_sensor: str | None = (
            None  # Entity ID of primary temp sensor (can be thermostat or temp sensor)
        )

    def add_device(
        self, device_id: str, device_type: str, mqtt_topic: str | None = None
    ) -> None:
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
        _LOGGER.debug(
            "Added device %s (type: %s) to area %s",
            device_id,
            device_type,
            self.area_id,
        )

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
        temp_drop: float | None = None,
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
            _LOGGER.warning(
                "Window sensor %s already exists in area %s", entity_id, self.area_id
            )
            return

        sensor_config: dict[str, str | float] = {
            "entity_id": entity_id,
            "action_when_open": action_when_open,
        }
        if action_when_open == "reduce_temperature":
            sensor_config["temp_drop"] = (
                temp_drop if temp_drop is not None else DEFAULT_WINDOW_OPEN_TEMP_DROP
            )

        self.window_sensors.append(sensor_config)
        _LOGGER.debug(
            "Added window sensor %s to area %s with action %s",
            entity_id,
            self.area_id,
            action_when_open,
        )

    def remove_window_sensor(self, entity_id: str) -> None:
        """Remove a window/door sensor from the area.

        Args:
            entity_id: Entity ID of the window/door sensor
        """
        self.window_sensors = [
            s for s in self.window_sensors if s.get("entity_id") != entity_id
        ]
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
            _LOGGER.warning(
                "Presence sensor %s already exists in area %s", entity_id, self.area_id
            )
            return

        sensor_config = {
            "entity_id": entity_id,
        }

        self.presence_sensors.append(sensor_config)
        _LOGGER.debug(
            "Added presence sensor %s to area %s (controls preset mode)",
            entity_id,
            self.area_id,
        )

    def remove_presence_sensor(self, entity_id: str) -> None:
        """Remove a presence/motion sensor from the area.

        Args:
            entity_id: Entity ID of the presence sensor
        """
        self.presence_sensors = [
            s for s in self.presence_sensors if s.get("entity_id") != entity_id
        ]
        _LOGGER.debug(
            "Removed presence sensor %s from area %s", entity_id, self.area_id
        )

    def get_preset_temperature(self) -> float:
        """Get the target temperature for the current preset mode.

        Returns:
            Temperature for current preset mode
        """
        # Determine which temperature to use based on use_global_* flags
        if self.area_manager:
            away_temp = (
                self.area_manager.global_away_temp
                if self.use_global_away
                else self.away_temp
            )
            eco_temp = (
                self.area_manager.global_eco_temp
                if self.use_global_eco
                else self.eco_temp
            )
            comfort_temp = (
                self.area_manager.global_comfort_temp
                if self.use_global_comfort
                else self.comfort_temp
            )
            home_temp = (
                self.area_manager.global_home_temp
                if self.use_global_home
                else self.home_temp
            )
            sleep_temp = (
                self.area_manager.global_sleep_temp
                if self.use_global_sleep
                else self.sleep_temp
            )
            activity_temp = (
                self.area_manager.global_activity_temp
                if self.use_global_activity
                else self.activity_temp
            )

            _LOGGER.debug(
                "Area %s: preset=%s, use_global_home=%s, global_home_temp=%.1f°C, area_home_temp=%.1f°C, selected_home_temp=%.1f°C",
                self.area_id,
                self.preset_mode,
                self.use_global_home,
                self.area_manager.global_home_temp,
                self.home_temp,
                home_temp,
            )
        else:
            # Fallback to area-specific temperatures if no area_manager
            _LOGGER.warning(
                "Area %s: No area_manager reference! Using fallback temps", self.area_id
            )
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
        _LOGGER.debug(
            "Area %s: get_preset_temperature() returning %.1f°C", self.area_id, result
        )
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
            self.area_id,
            old_mode,
            preset_mode,
            old_effective,
            new_effective,
            self.target_temperature,
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
        _LOGGER.info(
            "Activated boost mode for area %s: %d minutes at %.1f°C",
            self.area_id,
            duration,
            self.boost_temp,
        )

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
        _LOGGER.debug(
            "Added schedule %s to area %s", schedule.schedule_id, self.area_id
        )

    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule from the area.

        Args:
            schedule_id: Schedule identifier
        """
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            _LOGGER.debug("Removed schedule %s from area %s", schedule_id, self.area_id)

    def get_active_schedule_temperature(
        self, current_time: datetime | None = None
    ) -> float | None:
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
            s for s in self.schedules.values() if s.is_active(current_time)
        ]

        if not active_schedules:
            return None

        # Sort by time and get the latest
        active_schedules.sort(key=lambda s: s.time, reverse=True)
        return active_schedules[0].temperature

    def _get_window_open_temperature(self) -> Optional[float]:
        """Get temperature when window is open based on sensor actions.

        Returns:
            Temperature or None if no window action applies
        """
        if not self.window_is_open or len(self.window_sensors) == 0:
            return None

        # Find sensors with action_when_open configured
        for sensor in self.window_sensors:
            action = sensor.get("action_when_open", "reduce_temperature")
            if action == "turn_off":
                return 5.0  # Turn off heating (frost protection)
            elif action == "reduce_temperature":
                temp_drop = sensor.get("temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP)
                return max(5.0, self.target_temperature - temp_drop)
            # "none" action means no temperature change

        return None

    def _get_base_target_from_preset_or_schedule(
        self, current_time: datetime
    ) -> tuple[float, str]:
        """Get base target temperature from preset or schedule.

        Args:
            current_time: Current time

        Returns:
            Tuple of (temperature, source_description)
        """
        # Priority 1: Preset mode temperature
        if self.preset_mode != PRESET_NONE and self.preset_mode != PRESET_BOOST:
            target = self.get_preset_temperature()
            source = f"preset:{self.preset_mode}"
            return target, source

        # Priority 2: Schedule temperature (if available)
        target = self.get_active_schedule_temperature(current_time)
        if target is not None:
            return target, "schedule"

        # Priority 3: Base target temperature
        return self.target_temperature, "base_target"

    def _is_in_time_period(
        self, current_time: datetime, start_time_str: str, end_time_str: str
    ) -> bool:
        """Check if current time is within a time period.

        Handles periods that cross midnight.

        Args:
            current_time: Current datetime
            start_time_str: Start time as "HH:MM"
            end_time_str: End time as "HH:MM"

        Returns:
            True if current time is in period
        """
        start_hour, start_min = map(int, start_time_str.split(":"))
        end_hour, end_min = map(int, end_time_str.split(":"))
        current_hour = current_time.hour
        current_min = current_time.minute

        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        current_minutes = current_hour * 60 + current_min

        if start_minutes <= end_minutes:
            # Normal period (e.g., 08:00-18:00)
            return start_minutes <= current_minutes < end_minutes
        else:
            # Period crosses midnight (e.g., 22:00-06:00)
            return current_minutes >= start_minutes or current_minutes < end_minutes

    def _apply_night_boost(self, target: float, current_time: datetime) -> float:
        """Apply night boost to target temperature if applicable.

        Night boost adds a small temperature offset during configured hours to
        pre-heat the space before the morning schedule. It works additively on
        top of any active schedule (e.g., sleep preset).

        Args:
            target: Current target temperature
            current_time: Current time

        Returns:
            Adjusted temperature with night boost
        """
        if not self.night_boost_enabled:
            return target

        # Check if current time is within night boost period
        is_active = self._is_in_time_period(
            current_time, self.night_boost_start_time, self.night_boost_end_time
        )

        if is_active:
            old_target = target
            target += self.night_boost_offset
            _LOGGER.info(
                "Night boost active for %s (%s-%s): %.1f°C + %.1f°C = %.1f°C",
                self.area_id,
                self.night_boost_start_time,
                self.night_boost_end_time,
                old_target,
                self.night_boost_offset,
                target,
            )
            # Log to area logger if available
            if self.area_manager and hasattr(self.area_manager, "hass"):
                area_logger = self.area_manager.hass.data.get("smart_heating", {}).get(
                    "area_logger"
                )
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
                            "current_time": f"{current_time.hour:02d}:{current_time.minute:02d}",
                        },
                    )
        else:
            _LOGGER.debug(
                "Night boost inactive for %s at %02d:%02d (period: %s-%s)",
                self.area_id,
                current_time.hour,
                current_time.minute,
                self.night_boost_start_time,
                self.night_boost_end_time,
            )

        return target

    def get_effective_target_temperature(
        self, current_time: datetime | None = None
    ) -> float:
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
        window_temp = self._get_window_open_temperature()
        if window_temp is not None:
            return window_temp

        # Priority 3-5: Get base target from preset or schedule
        target, source = self._get_base_target_from_preset_or_schedule(current_time)

        # Log what we're starting with for debugging
        _LOGGER.debug(
            "Effective temp calculation for %s: source=%s, target=%.1f°C",
            self.area_id,
            source,
            target,
        )

        # Priority 6: Apply night boost if enabled (additive)
        target = self._apply_night_boost(target, current_time)

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
        if hasattr(self, "_state"):
            return self._state

        # Fallback to temperature-based state
        if (
            self._current_temperature is not None
            and self.target_temperature is not None
        ):
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
            "boost_end_time": (
                self.boost_end_time.isoformat() if self.boost_end_time else None
            ),
            # HVAC mode
            "hvac_mode": self.hvac_mode,
            # Window sensors (new structure)
            "window_sensors": self.window_sensors,
            # Presence sensors (new structure)
            "presence_sensors": self.presence_sensors,
            "use_global_presence": self.use_global_presence,
            # Auto preset mode
            "auto_preset_enabled": self.auto_preset_enabled,
            "auto_preset_home": self.auto_preset_home,
            "auto_preset_away": self.auto_preset_away,
            # Hysteresis override
            "hysteresis_override": self.hysteresis_override,
            # Primary temperature sensor
            "primary_temperature_sensor": self.primary_temperature_sensor,
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
        area.night_boost_start_time = data.get(
            "night_boost_start_time", DEFAULT_NIGHT_BOOST_START_TIME
        )
        area.night_boost_end_time = data.get(
            "night_boost_end_time", DEFAULT_NIGHT_BOOST_END_TIME
        )
        area.smart_night_boost_enabled = data.get("smart_night_boost_enabled", False)
        area.smart_night_boost_target_time = data.get(
            "smart_night_boost_target_time", "06:00"
        )
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

        # Primary temperature sensor
        area.primary_temperature_sensor = data.get("primary_temperature_sensor")

        # Window sensors - support both old string format and new dict format
        window_sensors_data = data.get("window_sensors", [])
        if window_sensors_data and isinstance(window_sensors_data[0], str):
            # Legacy format: convert to new format
            area.window_sensors = [
                {
                    "entity_id": entity_id,
                    "action_when_open": "reduce_temperature",
                    "temp_drop": data.get(
                        "window_open_temp_drop", DEFAULT_WINDOW_OPEN_TEMP_DROP
                    ),
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
                    "temp_boost_when_home": data.get(
                        "presence_temp_boost", DEFAULT_PRESENCE_TEMP_BOOST
                    ),
                }
                for entity_id in presence_sensors_data
            ]
        else:
            area.presence_sensors = presence_sensors_data

        # Global presence flag (default to False for backward compatibility)
        area.use_global_presence = data.get("use_global_presence", False)

        # Auto preset mode (default to False for backward compatibility)
        area.auto_preset_enabled = data.get("auto_preset_enabled", False)
        area.auto_preset_home = data.get("auto_preset_home", PRESET_HOME)
        area.auto_preset_away = data.get("auto_preset_away", PRESET_AWAY)

        # Load schedules
        for schedule_data in data.get("schedules", []):
            schedule = Schedule.from_dict(schedule_data)
            area.schedules[schedule.schedule_id] = schedule

        return area
