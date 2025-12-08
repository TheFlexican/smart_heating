"""Zone Manager for Smart Heating integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_ACTIVITY_TEMP,
    DEFAULT_AWAY_TEMP,
    DEFAULT_COMFORT_TEMP,
    DEFAULT_ECO_TEMP,
    DEFAULT_FROST_PROTECTION_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_SLEEP_TEMP,
    DEFAULT_TRV_HEATING_TEMP,
    DEFAULT_TRV_IDLE_TEMP,
    DEFAULT_TRV_TEMP_OFFSET,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .models import Area, Schedule

_LOGGER = logging.getLogger(__name__)


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

        # Safety Sensors (smoke/CO detectors) - Multi-sensor support
        self.safety_sensors: list[dict] = []  # List of safety sensor configurations
        # Legacy single sensor attributes (kept for backward compatibility migration)
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
            self.frost_protection_temp = data.get(
                "frost_protection_temp", DEFAULT_FROST_PROTECTION_TEMP
            )
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
                self.safety_sensors = [
                    {
                        "sensor_id": data.get("safety_sensor_id"),
                        "attribute": data.get("safety_sensor_attribute", "smoke"),
                        "alert_value": data.get("safety_sensor_alert_value", True),
                        "enabled": data.get("safety_sensor_enabled", True),
                    }
                ]
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
            "areas": [area.to_dict() for area in self.areas.values()],
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
            area_id,
            old_temp,
            temperature,
            area.preset_mode,
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
        _LOGGER.info(
            "OpenTherm gateway set to %s (enabled: %s)", gateway_id, self.opentherm_enabled
        )

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
                    sensor_id,
                    attribute,
                    alert_value,
                    enabled,
                )
                return

        # Add new sensor
        self.safety_sensors.append(
            {
                "sensor_id": sensor_id,
                "attribute": attribute,
                "alert_value": alert_value,
                "enabled": enabled,
            }
        )
        _LOGGER.info(
            "Safety sensor added: %s (attribute: %s, alert_value: %s, enabled: %s)",
            sensor_id,
            attribute,
            alert_value,
            enabled,
        )

    def remove_safety_sensor(self, sensor_id: str) -> None:
        """Remove a safety sensor by ID.

        Args:
            sensor_id: Entity ID of the safety sensor to remove
        """
        self.safety_sensors = [s for s in self.safety_sensors if s["sensor_id"] != sensor_id]
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
                    sensor_id,
                    attribute,
                    current_value,
                )
                return True, sensor_id

        # No sensors in alert state
        return False, None

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

    def set_trv_temperatures(
        self, heating_temp: float, idle_temp: float, temp_offset: float | None = None
    ) -> None:
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
                heating_temp,
                idle_temp,
                temp_offset,
            )
        else:
            _LOGGER.info(
                "TRV temperatures set: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp
            )
