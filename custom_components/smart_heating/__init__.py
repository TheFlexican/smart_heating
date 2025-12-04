"""The Smart Heating integration."""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_DEVICE_ID,
    ATTR_DEVICE_TYPE,
    ATTR_ENABLED,
    ATTR_TEMPERATURE,
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_DEVICE_TO_AREA,
    SERVICE_CREATE_AREA,
    SERVICE_DELETE_AREA,
    SERVICE_DISABLE_AREA,
    SERVICE_ENABLE_AREA,
    SERVICE_REFRESH,
    SERVICE_REMOVE_DEVICE_FROM_AREA,
    SERVICE_SET_AREA_TEMPERATURE,
)
from .coordinator import SmartHeatingCoordinator
from .area_manager import AreaManager
from .api import async_setup_api
from .websocket import async_setup_websocket

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Heating from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        bool: True if setup was successful
    """
    _LOGGER.debug("Setting up Smart Heating integration")
    
    # Create zone manager
    area_manager = AreaManager(hass)
    await area_manager.async_load()
    
    # Create coordinator instance
    coordinator = SmartHeatingCoordinator(hass, area_manager)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    _LOGGER.debug("Smart Heating coordinator stored in hass.data")
    
    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up REST API and WebSocket
    async_setup_api(hass, area_manager)
    async_setup_websocket(hass, area_manager)
    
    # Register static path for frontend
    hass.http.register_static_path(
        "/smart_heating",
        hass.config.path("custom_components/smart_heating/frontend/dist"),
        True
    )
    
    # Register sidebar panel
    await hass.components.frontend.async_register_built_in_panel(
        component_name="custom",
        sidebar_title="Smart Heating",
        sidebar_icon="mdi:radiator",
        frontend_url_path="smart_heating",
        config={"url": "/smart_heating_ui"},
        require_admin=False,
    )
    
    # Register services
    await async_setup_services(hass, coordinator)
    
    _LOGGER.info("Smart Heating integration setup complete")
    
    return True


async def async_setup_services(hass: HomeAssistant, coordinator: SmartHeatingCoordinator) -> None:
    """Set up services for Smart Heating.
    
    Args:
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    area_manager = coordinator.area_manager
    
    async def async_handle_refresh(call: ServiceCall) -> None:
        """Handle the refresh service call."""
        _LOGGER.debug("Refresh service called")
        await coordinator.async_request_refresh()
        _LOGGER.info("Smart Heating data refreshed")
    
    async def async_handle_create_zone(call: ServiceCall) -> None:
        """Handle the create_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        zone_name = call.data[ATTR_AREA_NAME]
        temperature = call.data.get(ATTR_TEMPERATURE, 20.0)
        
        _LOGGER.debug("Creating zone %s (%s) with temperature %.1f°C", area_id, area_name, temperature)
        
        try:
            area_manager.create_area(area_id, area_name, temperature)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Created zone %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to create area: %s", err)
    
    async def async_handle_delete_zone(call: ServiceCall) -> None:
        """Handle the delete_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Deleting zone %s", area_id)
        
        try:
            area_manager.delete_area(area_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Deleted zone %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to delete area: %s", err)
    
    async def async_handle_add_device(call: ServiceCall) -> None:
        """Handle the add_device_to_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        device_type = call.data[ATTR_DEVICE_TYPE]
        
        _LOGGER.debug("Adding device %s (type: %s) to zone %s", device_id, device_type, area_id)
        
        try:
            area_manager.add_device_to_area(area_id, device_id, device_type)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added device %s to zone %s", device_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to add device: %s", err)
    
    async def async_handle_remove_device(call: ServiceCall) -> None:
        """Handle the remove_device_from_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        
        _LOGGER.debug("Removing device %s from zone %s", device_id, area_id)
        
        try:
            area_manager.remove_device_from_area(area_id, device_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed device %s from zone %s", device_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove device: %s", err)
    
    async def async_handle_set_temperature(call: ServiceCall) -> None:
        """Handle the set_zone_temperature service call."""
        area_id = call.data[ATTR_AREA_ID]
        temperature = call.data[ATTR_TEMPERATURE]
        
        _LOGGER.debug("Setting zone %s temperature to %.1f°C", area_id, temperature)
        
        try:
            area_manager.set_area_target_temperature(area_id, temperature)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set zone %s temperature to %.1f°C", area_id, temperature)
        except ValueError as err:
            _LOGGER.error("Failed to set temperature: %s", err)
    
    async def async_handle_enable_zone(call: ServiceCall) -> None:
        """Handle the enable_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Enabling zone %s", area_id)
        
        try:
            area_manager.enable_area(area_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Enabled zone %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to enable area: %s", err)
    
    async def async_handle_disable_zone(call: ServiceCall) -> None:
        """Handle the disable_zone service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Disabling zone %s", area_id)
        
        try:
            area_manager.disable_area(area_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Disabled zone %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to disable area: %s", err)
    
    # Service schemas
    CREATE_ZONE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_AREA_NAME): cv.string,
        vol.Optional(ATTR_TEMPERATURE, default=20.0): vol.Coerce(float),
    })
    
    DELETE_ZONE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
    })
    
    ADD_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_DEVICE_TYPE): vol.In([
            DEVICE_TYPE_THERMOSTAT,
            DEVICE_TYPE_TEMPERATURE_SENSOR,
            DEVICE_TYPE_OPENTHERM_GATEWAY,
            DEVICE_TYPE_VALVE,
        ]),
    })
    
    REMOVE_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_DEVICE_ID): cv.string,
    })
    
    SET_TEMPERATURE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
    })
    
    ZONE_ID_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
    })
    
    # Register all services
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, async_handle_refresh)
    hass.services.async_register(DOMAIN, SERVICE_CREATE_AREA, async_handle_create_zone, schema=CREATE_ZONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_AREA, async_handle_delete_zone, schema=DELETE_ZONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_DEVICE_TO_AREA, async_handle_add_device, schema=ADD_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_AREA, async_handle_remove_device, schema=REMOVE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_AREA_TEMPERATURE, async_handle_set_temperature, schema=SET_TEMPERATURE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_AREA, async_handle_enable_zone, schema=ZONE_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_AREA, async_handle_disable_zone, schema=ZONE_ID_SCHEMA)
    
    _LOGGER.debug("All services registered")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        bool: True if unload was successful
    """
    _LOGGER.debug("Unloading Smart Heating integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Smart Heating coordinator removed from hass.data")
        
        # Remove sidebar panel
        try:
            await hass.components.frontend.async_remove_panel("smart_heating")
            _LOGGER.debug("Smart Heating panel removed from sidebar")
        except Exception as err:
            _LOGGER.warning("Failed to remove panel: %s", err)
        
        # Remove services if no more instances
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
            hass.services.async_remove(DOMAIN, SERVICE_CREATE_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_DEVICE_TO_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_SET_AREA_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_AREA)
            _LOGGER.debug("Smart Heating services removed")
    
    _LOGGER.info("Smart Heating integration unloaded")
    
    return unload_ok
