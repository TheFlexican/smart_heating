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
from .models import Area

_LOGGER = logging.getLogger(__name__)


# noqa: ASYNC109 - Home Assistant platform setup must be async
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
    
    # Create climate entities for each area
    entities = []
    for area_id, area in area_manager.get_all_areas().items():
        entities.append(AreaClimate(coordinator, entry, area))
    
    # Add entities
    async_add_entities(entities)
    _LOGGER.info("Smart Heating climate platform setup complete with %d areas", len(entities))


class AreaClimate(CoordinatorEntity, ClimateEntity):
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
        area: Area,
    ) -> None:
        """Initialize the climate entity.
        
        Args:
            coordinator: The data update coordinator
            entry: Config entry
            area: Area instance
        """
        super().__init__(coordinator)
        
        self._area = area
        
        # Entity attributes
        self._attr_name = f"Zone {area.name}"
        self._attr_unique_id = f"{entry.entry_id}_climate_{area.area_id}"
        self._attr_icon = "mdi:thermostat"
        
        _LOGGER.debug(
            "AreaClimate initialized for area %s with unique_id: %s",
            area.area_id,
            self._attr_unique_id,
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature.
        
        Returns:
            Current temperature or None
        """
        return self._area.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature.
        
        Returns:
            Target temperature or None
        """
        return self._area.target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode.
        
        Returns:
            Current HVAC mode
        """
        if self._area.enabled:
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
        
        _LOGGER.debug("Setting area %s temperature to %.1f°C", self._area.area_id, temperature)
        
        # Update area manager
        self.coordinator.area_manager.set_area_target_temperature(
            self._area.area_id, temperature
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
        _LOGGER.debug("Setting area %s HVAC mode to %s", self._area.area_id, hvac_mode)
        
        if hvac_mode == HVACMode.HEAT:
            self.coordinator.area_manager.enable_area(self._area.area_id)
        elif hvac_mode == HVACMode.OFF:
            self.coordinator.area_manager.disable_area(self._area.area_id)
        
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
            "area_id": self._area.area_id,
            "area_name": self._area.name,
            "area_state": self._area.state,
            "device_count": len(self._area.devices),
            "devices": list(self._area.devices.keys()),
        }
        
        # Add device type counts
        thermostats = self._area.get_thermostats()
        temp_sensors = self._area.get_temperature_sensors()
        opentherm_gateways = self._area.get_opentherm_gateways()
        
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
