"""The Zone Heater Manager integration."""
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
    ATTR_ZONE_ID,
    ATTR_ZONE_NAME,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_DEVICE_TO_ZONE,
    SERVICE_CREATE_ZONE,
    SERVICE_DELETE_ZONE,
    SERVICE_DISABLE_ZONE,
    SERVICE_ENABLE_ZONE,
    SERVICE_REFRESH,
    SERVICE_REMOVE_DEVICE_FROM_ZONE,
    SERVICE_SET_ZONE_TEMPERATURE,
)
from .coordinator import ZoneHeaterManagerCoordinator
from .zone_manager import ZoneManager
from .api import async_setup_api
from .websocket import async_setup_websocket

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zone Heater Manager from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        bool: True if setup was successful
    """
    _LOGGER.debug("Setting up Zone Heater Manager integration")
    
    # Create zone manager
    zone_manager = ZoneManager(hass)
    await zone_manager.async_load()
    
    # Create coordinator instance
    coordinator = ZoneHeaterManagerCoordinator(hass, zone_manager)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    _LOGGER.debug("Zone Heater Manager coordinator stored in hass.data")
    
    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up REST API and WebSocket
    async_setup_api(hass, zone_manager)
    async_setup_websocket(hass, zone_manager)
    
    # Register static path for frontend
    hass.http.register_static_path(
        "/zone_heater_manager",
        hass.config.path("custom_components/zone_heater_manager/frontend/dist"),
        True
    )
    
    # Register sidebar panel
    await hass.components.frontend.async_register_built_in_panel(
        component_name="custom",
        sidebar_title="Zone Heater Manager",
        sidebar_icon="mdi:radiator",
        frontend_url_path="zone_heater_manager",
        config={
            "_panel_custom": {
                "name": "zone-heater-manager-panel",
                "embed_iframe": True,
                "trust_external": False,
            }
        },
        require_admin=False,
    )
    
    # Register services
    await async_setup_services(hass, coordinator)
    
    _LOGGER.info("Zone Heater Manager integration setup complete")
    
    return True


async def async_setup_services(hass: HomeAssistant, coordinator: ZoneHeaterManagerCoordinator) -> None:
    """Set up services for Zone Heater Manager.
    
    Args:
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    zone_manager = coordinator.zone_manager
    
    async def async_handle_refresh(call: ServiceCall) -> None:
        """Handle the refresh service call."""
        _LOGGER.debug("Refresh service called")
        await coordinator.async_request_refresh()
        _LOGGER.info("Zone Heater Manager data refreshed")
    
    async def async_handle_create_zone(call: ServiceCall) -> None:
        """Handle the create_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        zone_name = call.data[ATTR_ZONE_NAME]
        temperature = call.data.get(ATTR_TEMPERATURE, 20.0)
        
        _LOGGER.debug("Creating zone %s (%s) with temperature %.1f°C", zone_id, zone_name, temperature)
        
        try:
            zone_manager.create_zone(zone_id, zone_name, temperature)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Created zone %s", zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to create zone: %s", err)
    
    async def async_handle_delete_zone(call: ServiceCall) -> None:
        """Handle the delete_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        
        _LOGGER.debug("Deleting zone %s", zone_id)
        
        try:
            zone_manager.delete_zone(zone_id)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Deleted zone %s", zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to delete zone: %s", err)
    
    async def async_handle_add_device(call: ServiceCall) -> None:
        """Handle the add_device_to_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        device_type = call.data[ATTR_DEVICE_TYPE]
        
        _LOGGER.debug("Adding device %s (type: %s) to zone %s", device_id, device_type, zone_id)
        
        try:
            zone_manager.add_device_to_zone(zone_id, device_id, device_type)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added device %s to zone %s", device_id, zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to add device: %s", err)
    
    async def async_handle_remove_device(call: ServiceCall) -> None:
        """Handle the remove_device_from_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        
        _LOGGER.debug("Removing device %s from zone %s", device_id, zone_id)
        
        try:
            zone_manager.remove_device_from_zone(zone_id, device_id)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed device %s from zone %s", device_id, zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove device: %s", err)
    
    async def async_handle_set_temperature(call: ServiceCall) -> None:
        """Handle the set_zone_temperature service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        temperature = call.data[ATTR_TEMPERATURE]
        
        _LOGGER.debug("Setting zone %s temperature to %.1f°C", zone_id, temperature)
        
        try:
            zone_manager.set_zone_target_temperature(zone_id, temperature)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set zone %s temperature to %.1f°C", zone_id, temperature)
        except ValueError as err:
            _LOGGER.error("Failed to set temperature: %s", err)
    
    async def async_handle_enable_zone(call: ServiceCall) -> None:
        """Handle the enable_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        
        _LOGGER.debug("Enabling zone %s", zone_id)
        
        try:
            zone_manager.enable_zone(zone_id)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Enabled zone %s", zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to enable zone: %s", err)
    
    async def async_handle_disable_zone(call: ServiceCall) -> None:
        """Handle the disable_zone service call."""
        zone_id = call.data[ATTR_ZONE_ID]
        
        _LOGGER.debug("Disabling zone %s", zone_id)
        
        try:
            zone_manager.disable_zone(zone_id)
            await zone_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Disabled zone %s", zone_id)
        except ValueError as err:
            _LOGGER.error("Failed to disable zone: %s", err)
    
    # Service schemas
    CREATE_ZONE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
        vol.Required(ATTR_ZONE_NAME): cv.string,
        vol.Optional(ATTR_TEMPERATURE, default=20.0): vol.Coerce(float),
    })
    
    DELETE_ZONE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
    })
    
    ADD_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_DEVICE_TYPE): vol.In([
            DEVICE_TYPE_THERMOSTAT,
            DEVICE_TYPE_TEMPERATURE_SENSOR,
            DEVICE_TYPE_OPENTHERM_GATEWAY,
            DEVICE_TYPE_VALVE,
        ]),
    })
    
    REMOVE_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
        vol.Required(ATTR_DEVICE_ID): cv.string,
    })
    
    SET_TEMPERATURE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
        vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
    })
    
    ZONE_ID_SCHEMA = vol.Schema({
        vol.Required(ATTR_ZONE_ID): cv.string,
    })
    
    # Register all services
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, async_handle_refresh)
    hass.services.async_register(DOMAIN, SERVICE_CREATE_ZONE, async_handle_create_zone, schema=CREATE_ZONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_ZONE, async_handle_delete_zone, schema=DELETE_ZONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_DEVICE_TO_ZONE, async_handle_add_device, schema=ADD_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_ZONE, async_handle_remove_device, schema=REMOVE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_ZONE_TEMPERATURE, async_handle_set_temperature, schema=SET_TEMPERATURE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_ZONE, async_handle_enable_zone, schema=ZONE_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_ZONE, async_handle_disable_zone, schema=ZONE_ID_SCHEMA)
    
    _LOGGER.debug("All services registered")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        bool: True if unload was successful
    """
    _LOGGER.debug("Unloading Zone Heater Manager integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Zone Heater Manager coordinator removed from hass.data")
        
        # Remove sidebar panel
        try:
            await hass.components.frontend.async_remove_panel("zone_heater_manager")
            _LOGGER.debug("Zone Heater Manager panel removed from sidebar")
        except Exception as err:
            _LOGGER.warning("Failed to remove panel: %s", err)
        
        # Remove services if no more instances
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
            hass.services.async_remove(DOMAIN, SERVICE_CREATE_ZONE)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_ZONE)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_DEVICE_TO_ZONE)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_ZONE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_ZONE_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_ZONE)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_ZONE)
            _LOGGER.debug("Zone Heater Manager services removed")
    
    _LOGGER.info("Zone Heater Manager integration unloaded")
    
    return unload_ok
