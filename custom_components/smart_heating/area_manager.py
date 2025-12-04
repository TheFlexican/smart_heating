"""Zone Manager for Smart Heating integration."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_DEVICES,
    ATTR_ENABLED,
    ATTR_TARGET_TEMPERATURE,
    ATTR_ZONE_ID,
    ATTR_ZONE_NAME,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    STATE_HEATING,
    STATE_IDLE,
    STATE_OFF,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class Area:
    """Representation of a heating zone."""

    def __init__(
        self,
        area_id: str,
        name: str,
        target_temperature: float = 20.0,
        enabled: bool = True,
    ) -> None:
        """Initialize a zone.
        
        Args:
            area_id: Unique identifier for the zone
            name: Display name of the zone
            target_temperature: Target temperature for the zone
            enabled: Whether the zone is enabled
        """
        self.area_id = area_id
        self.name = name
        self.target_temperature = target_temperature
        self.enabled = enabled
        self.devices: dict[str, dict[str, Any]] = {}
        self._current_temperature: float | None = None

    def add_device(self, device_id: str, device_type: str, mqtt_topic: str | None = None) -> None:
        """Add a device to the zone.
        
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
        _LOGGER.debug("Added device %s (type: %s) to zone %s", device_id, device_type, self.area_id)

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the zone.
        
        Args:
            device_id: Unique identifier for the device
        """
        if device_id in self.devices:
            del self.devices[device_id]
            _LOGGER.debug("Removed device %s from zone %s", device_id, self.area_id)

    def get_temperature_sensors(self) -> list[str]:
        """Get all temperature sensor device IDs in the zone.
        
        Returns:
            List of temperature sensor device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_TEMPERATURE_SENSOR
        ]

    def get_thermostats(self) -> list[str]:
        """Get all thermostat device IDs in the zone.
        
        Returns:
            List of thermostat device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_THERMOSTAT
        ]

    def get_opentherm_gateways(self) -> list[str]:
        """Get all OpenTherm gateway device IDs in the zone.
        
        Returns:
            List of OpenTherm gateway device IDs
        """
        return [
            device_id
            for device_id, device in self.devices.items()
            if device["type"] == DEVICE_TYPE_OPENTHERM_GATEWAY
        ]

    @property
    def current_temperature(self) -> float | None:
        """Get the current temperature of the zone.
        
        Returns:
            Current temperature or None
        """
        return self._current_temperature

    @current_temperature.setter
    def current_temperature(self, value: float | None) -> None:
        """Set the current temperature of the zone.
        
        Args:
            value: New temperature value
        """
        self._current_temperature = value

    @property
    def state(self) -> str:
        """Get the current state of the zone.
        
        Returns:
            Current state (heating, idle, off)
        """
        if not self.enabled:
            return STATE_OFF
        
        if self._current_temperature is not None and self.target_temperature is not None:
            if self._current_temperature < self.target_temperature - 0.5:
                return STATE_HEATING
        
        return STATE_IDLE

    def to_dict(self) -> dict[str, Any]:
        """Convert zone to dictionary for storage.
        
        Returns:
            Dictionary representation of the zone
        """
        return {
            ATTR_ZONE_ID: self.area_id,
            ATTR_ZONE_NAME: self.name,
            ATTR_TARGET_TEMPERATURE: self.target_temperature,
            ATTR_ENABLED: self.enabled,
            ATTR_DEVICES: self.devices,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Zone":
        """Create a zone from dictionary.
        
        Args:
            data: Dictionary with zone data
            
        Returns:
            Zone instance
        """
        zone = cls(
            area_id=data[ATTR_ZONE_ID],
            name=data[ATTR_ZONE_NAME],
            target_temperature=data.get(ATTR_TARGET_TEMPERATURE, 20.0),
            enabled=data.get(ATTR_ENABLED, True),
        )
        zone.devices = data.get(ATTR_DEVICES, {})
        return zone


class AreaManager:
    """Manage heating zones."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the zone manager.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.zones: dict[str, Area] = {}
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        _LOGGER.debug("AreaManager initialized")

    async def async_load(self) -> None:
        """Load zones from storage."""
        _LOGGER.debug("Loading zones from storage")
        data = await self._store.async_load()
        
        if data is not None and "zones" in data:
            for zone_data in data["zones"]:
                zone = Zone.from_dict(area_data)
                self.zones[area.area_id] = zone
            _LOGGER.info("Loaded %d zones from storage", len(self.zones))
        else:
            _LOGGER.debug("No zones found in storage")

    async def async_save(self) -> None:
        """Save zones to storage."""
        _LOGGER.debug("Saving zones to storage")
        data = {
            "zones": [area.to_dict() for zone in self.zones.values()]
        }
        await self._store.async_save(data)
        _LOGGER.info("Saved %d zones to storage", len(self.zones))

    def create_area(self, area_id: str, name: str, target_temperature: float = 20.0) -> Area:
        """Create a new zone.
        
        Args:
            area_id: Unique identifier for the zone
            name: Display name of the zone
            target_temperature: Target temperature for the zone
            
        Returns:
            Created zone
            
        Raises:
            ValueError: If zone already exists
        """
        if area_id in self.zones:
            raise ValueError(f"Zone {area_id} already exists")
        
        zone = Zone(area_id, name, target_temperature)
        self.zones[area_id] = zone
        _LOGGER.info("Created zone %s (%s)", area_id, name)
        return zone

    def delete_area(self, area_id: str) -> None:
        """Delete a zone.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If zone does not exist
        """
        if area_id not in self.zones:
            raise ValueError(f"Zone {area_id} does not exist")
        
        del self.zones[area_id]
        _LOGGER.info("Deleted zone %s", area_id)

    def get_area(self, area_id: str) -> Area | None:
        """Get a zone by ID.
        
        Args:
            area_id: Zone identifier
            
        Returns:
            Zone or None if not found
        """
        return self.zones.get(area_id)

    def get_all_areas(self) -> dict[str, Area]:
        """Get all zones.
        
        Returns:
            Dictionary of all zones
        """
        return self.zones

    def add_device_to_area(
        self,
        area_id: str,
        device_id: str,
        device_type: str,
        mqtt_topic: str | None = None,
    ) -> None:
        """Add a device to a zone.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            device_type: Type of device
            mqtt_topic: MQTT topic for the device
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.add_device(device_id, device_type, mqtt_topic)

    def remove_device_from_area(self, area_id: str, device_id: str) -> None:
        """Remove a device from a zone.
        
        Args:
            area_id: Zone identifier
            device_id: Device identifier
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.remove_device(device_id)

    def update_area_temperature(self, area_id: str, temperature: float) -> None:
        """Update the current temperature of a zone.
        
        Args:
            area_id: Zone identifier
            temperature: New temperature value
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.current_temperature = temperature
        _LOGGER.debug("Updated zone %s temperature to %.1f°C", area_id, temperature)

    def set_area_target_temperature(self, area_id: str, temperature: float) -> None:
        """Set the target temperature of a zone.
        
        Args:
            area_id: Zone identifier
            temperature: Target temperature
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.target_temperature = temperature
        _LOGGER.info("Set zone %s target temperature to %.1f°C", area_id, temperature)

    def enable_area(self, area_id: str) -> None:
        """Enable a zone.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.enabled = True
        _LOGGER.info("Enabled zone %s", area_id)

    def disable_area(self, area_id: str) -> None:
        """Disable a zone.
        
        Args:
            area_id: Zone identifier
            
        Raises:
            ValueError: If zone does not exist
        """
        zone = self.get_zone(area_id)
        if zone is None:
            raise ValueError(f"Zone {area_id} does not exist")
        
        zone.enabled = False
        _LOGGER.info("Disabled zone %s", area_id)
