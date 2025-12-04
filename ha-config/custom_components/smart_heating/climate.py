"""Climate platform for Smart Heating integration."""
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    """Set up Smart Heating climate platform.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    _LOGGER.debug("Setting up Smart Heating climate platform")
    
    # Get the coordinator from hass.data
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry.entry_id]
    area_manager = coordinator.area_manager
    
    # Create climate entities for each zone
    entities = []
    for area_id, area in area_manager.get_all_areas().items():
        entities.append(AreaClimate(coordinator, entry, area))
    
    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Smart Heating climate platform setup complete with %d zones", len(entities))


class ZoneClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Zone Climate control."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_min_temp = 5.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 0.5

    def __init__(
        self,
        coordinator: SmartHeatingCoordinator,
        entry: ConfigEntry,
        area: Zone,
    ) -> None:
        """Initialize the climate entity.
        
        Args:
            coordinator: The data update coordinator
            entry: Config entry
            area: Zone instance
        """
        super().__init__(coordinator)
        
        self._zone = zone
        
        # Entity attributes
        self._attr_name = f"Zone {zone.name}"
        self._attr_unique_id = f"{entry.entry_id}_climate_{zone.area_id}"
        self._attr_icon = "mdi:thermostat"
        
        _LOGGER.debug(
            "ZoneClimate initialized for zone %s with unique_id: %s",
            zone.area_id,
            self._attr_unique_id,
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature.
        
        Returns:
            Current temperature or None
        """
        return self._zone.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature.
        
        Returns:
            Target temperature or None
        """
        return self._zone.target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode.
        
        Returns:
            Current HVAC mode
        """
        if self._zone.enabled:
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature.
        
        Args:
            **kwargs: Keyword arguments containing temperature
        """
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        _LOGGER.debug("Setting zone %s temperature to %.1f°C", self._zone.area_id, temperature)
        
        # Update zone manager
        self.coordinator.area_manager.set_area_target_temperature(
            self._zone.area_id, temperature
        )
        
        # Save to storage
        await self.coordinator.area_manager.async_save()
        
        # Request coordinator refresh
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode.
        
        Args:
            hvac_mode: New HVAC mode
        """
        _LOGGER.debug("Setting zone %s HVAC mode to %s", self._zone.area_id, hvac_mode)
        
        if hvac_mode == HVACMode.HEAT:
            self.coordinator.area_manager.enable_area(self._zone.area_id)
        elif hvac_mode == HVACMode.OFF:
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
        attributes = {
            "area_id": self._zone.area_id,
            "zone_name": self._zone.name,
            "zone_state": self._zone.state,
            "device_count": len(self._zone.devices),
            "devices": list(self._zone.devices.keys()),
        }
        
        # Add device type counts
        thermostats = self._zone.get_thermostats()
        temp_sensors = self._zone.get_temperature_sensors()
        opentherm_gateways = self._zone.get_opentherm_gateways()
        
        if thermostats:
            attributes["thermostats"] = thermostats
        if temp_sensors:
            attributes["temperature_sensors"] = temp_sensors
        if opentherm_gateways:
            attributes["opentherm_gateways"] = opentherm_gateways
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available.
        
        Returns:
            bool: True if the coordinator has data
        """
        return self.coordinator.last_update_success
