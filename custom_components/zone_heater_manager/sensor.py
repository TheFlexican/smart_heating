"""Sensor platform for Zone Heater Manager integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_INITIALIZED
from .coordinator import ZoneHeaterManagerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zone Heater Manager sensor platform.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up Zone Heater Manager sensor platform")
    
    # Get the coordinator from hass.data
    coordinator: ZoneHeaterManagerCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Create sensor entities
    entities = [
        ZoneHeaterManagerStatusSensor(coordinator, entry),
    ]
    
    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Zone Heater Manager sensor platform setup complete")


class ZoneHeaterManagerStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Zone Heater Manager Status Sensor."""

    def __init__(
        self,
        coordinator: ZoneHeaterManagerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: The data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        
        # Entity attributes
        self._attr_name = "Zone Heater Manager Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:radiator"
        
        _LOGGER.debug("ZoneHeaterManagerStatusSensor initialized with unique_id: %s", self._attr_unique_id)

    @property
    def native_value(self) -> str:
        """Return the state of the sensor.
        
        Returns:
            str: The current status
        """
        # Get status from coordinator data
        if self.coordinator.data:
            status = self.coordinator.data.get("status", STATE_INITIALIZED)
            _LOGGER.debug("Sensor state: %s", status)
            return status
        
        _LOGGER.debug("No coordinator data, returning default state")
        return STATE_INITIALIZED

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes.
        
        Returns:
            dict: Additional attributes
        """
        attributes = {
            "integration": "zone_heater_manager",
            "version": "0.0.1",
        }
        
        # Add coordinator data to attributes if available
        if self.coordinator.data:
            attributes["last_update"] = self.coordinator.last_update_success_time
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Returns:
            bool: True if the coordinator has data
        """
        return self.coordinator.last_update_success
