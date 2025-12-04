"""Switch platform for Smart Heating integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartHeatingCoordinator
from .area_manager import Area

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Heating switch platform.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up Smart Heating switch platform")
    
    # Get the coordinator from hass.data
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry.entry_id]
    area_manager = coordinator.area_manager
    
    # Create switch entities for each zone
    entities = []
    for area_id, area in area_manager.get_all_areas().items():
        entities.append(AreaSwitch(coordinator, entry, area))
    
    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Smart Heating switch platform setup complete with %d zones", len(entities))


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Zone Switch."""

    def __init__(
        self,
        coordinator: SmartHeatingCoordinator,
        entry: ConfigEntry,
        area: Zone,
    ) -> None:
        """Initialize the switch entity.
        
        Args:
            coordinator: The data update coordinator
            entry: Config entry
            area: Zone instance
        """
        super().__init__(coordinator)
        
        self._zone = zone
        
        # Entity attributes
        self._attr_name = f"Zone {zone.name} Control"
        self._attr_unique_id = f"{entry.entry_id}_switch_{zone.area_id}"
        self._attr_icon = "mdi:radiator"
        
        _LOGGER.debug(
            "ZoneSwitch initialized for zone %s with unique_id: %s",
            zone.area_id,
            self._attr_unique_id,
        )

    @property
    def is_on(self) -> bool:
        """Return true if the zone is enabled.
        
        Returns:
            True if zone is enabled
        """
        return self._zone.enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the zone on.
        
        Args:
            **kwargs: Additional keyword arguments
        """
        _LOGGER.debug("Turning on zone %s", self._zone.area_id)
        
        self.coordinator.area_manager.enable_area(self._zone.area_id)
        
        # Save to storage
        await self.coordinator.area_manager.async_save()
        
        # Request coordinator refresh
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the zone off.
        
        Args:
            **kwargs: Additional keyword arguments
        """
        _LOGGER.debug("Turning off zone %s", self._zone.area_id)
        
        self.coordinator.area_manager.disable_area(self._zone.area_id)
        
        # Save to storage
        await self.coordinator.area_manager.async_save()
        
        # Request coordinator refresh
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes.
        
        Returns:
            Dictionary of additional attributes
        """
        return {
            "area_id": self._zone.area_id,
            "zone_name": self._zone.name,
            "zone_state": self._zone.state,
            "target_temperature": self._zone.target_temperature,
            "current_temperature": self._zone.current_temperature,
            "device_count": len(self._zone.devices),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Returns:
            bool: True if the coordinator has data
        """
        return self.coordinator.last_update_success
