"""Sensor platform for Smart Heating integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_INITIALIZED
from .coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


# noqa: ASYNC109 - Home Assistant platform setup must be async
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Heating sensor platform.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up Smart Heating sensor platform")
    
    # Get the coordinator from hass.data
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Create sensor entities
    entities = [
        SmartHeatingStatusSensor(coordinator, entry),
    ]
    
    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Smart Heating sensor platform setup complete")


class SmartHeatingStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Smart Heating Status Sensor."""

    def __init__(
        self,
        coordinator: SmartHeatingCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.
        
        Args:
            coordinator: The data update coordinator
            entry: Config entry
        """
        super().__init__(coordinator)
        
        # Entity attributes
        self._attr_name = "Smart Heating Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:radiator"
        
        _LOGGER.debug("SmartHeatingStatusSensor initialized with unique_id: %s", self._attr_unique_id)

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
            "integration": "smart_heating",
            "version": "2.0.0",
        }
        
        # Add coordinator data to attributes if available
        if self.coordinator.data:
            attributes["area_count"] = self.coordinator.data.get("area_count", 0)
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Returns:
            bool: True if the coordinator has data
        """
        return self.coordinator.last_update_success
