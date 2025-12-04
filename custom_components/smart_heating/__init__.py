"""The Smart Heating integration."""
import asyncio
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .const import (
    ATTR_DEVICE_ID,
    ATTR_DEVICE_TYPE,
    ATTR_ENABLED,
    ATTR_TEMPERATURE,
    ATTR_AREA_ID,
    ATTR_AREA_NAME,
    ATTR_SCHEDULE_ID,
    ATTR_TIME,
    ATTR_DAYS,
    ATTR_NIGHT_BOOST_ENABLED,
    ATTR_NIGHT_BOOST_OFFSET,
    ATTR_HYSTERESIS,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_DEVICE_TO_AREA,
    SERVICE_DISABLE_AREA,
    SERVICE_ENABLE_AREA,
    SERVICE_REFRESH,
    SERVICE_REMOVE_DEVICE_FROM_AREA,
    SERVICE_SET_AREA_TEMPERATURE,
    SERVICE_ADD_SCHEDULE,
    SERVICE_REMOVE_SCHEDULE,
    SERVICE_ENABLE_SCHEDULE,
    SERVICE_DISABLE_SCHEDULE,
    SERVICE_SET_NIGHT_BOOST,
    SERVICE_SET_HYSTERESIS,
)
from .coordinator import SmartHeatingCoordinator
from .area_manager import AreaManager
from .api import setup_api
from .websocket import setup_websocket
from .climate_controller import ClimateController
from .scheduler import ScheduleExecutor
from .history import HistoryTracker

_LOGGER = logging.getLogger(__name__)

# Update interval for climate control (30 seconds)
CLIMATE_UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Heating from a config entry.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
        
    Returns:
        bool: True if setup was successful
    """
    _LOGGER.debug("Setting up Smart Heating integration")
    
    # Initialize hass.data for this domain
    hass.data.setdefault(DOMAIN, {})
    
    # Create area manager
    area_manager = AreaManager(hass)
    await area_manager.async_load()
    
    # Create history tracker
    history_tracker = HistoryTracker(hass)
    await history_tracker.async_load()
    hass.data[DOMAIN]["history"] = history_tracker
    
    # Create coordinator instance
    coordinator = SmartHeatingCoordinator(hass, area_manager)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    _LOGGER.debug("Smart Heating coordinator stored in hass.data")
    
    # Create and start climate controller
    climate_controller = ClimateController(hass, area_manager)
    
    # Store climate controller
    hass.data[DOMAIN]["climate_controller"] = climate_controller
    
    # Set up periodic heating control (every 30 seconds)
    async def async_control_heating_wrapper(now):
        """Wrapper for periodic climate control."""
        try:
            await climate_controller.async_control_heating()
        except Exception as err:
            _LOGGER.error("Error in climate control: %s", err)
    
    # Start the periodic control
    hass.data[DOMAIN]["climate_unsub"] = async_track_time_interval(
        hass, async_control_heating_wrapper, CLIMATE_UPDATE_INTERVAL
    )
    
    # Run initial control after 5 seconds
    async def run_initial_control():
        await asyncio.sleep(5)
        await climate_controller.async_control_heating()
    
    hass.async_create_task(run_initial_control())
    
    _LOGGER.info("Climate controller started with 30-second update interval")
    
    # Create and start schedule executor
    schedule_executor = ScheduleExecutor(hass, area_manager)
    hass.data[DOMAIN]["schedule_executor"] = schedule_executor
    await schedule_executor.async_start()
    _LOGGER.info("Schedule executor started")
    
    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up REST API and WebSocket
    await setup_api(hass, area_manager)
    await setup_websocket(hass)
    
    # Register sidebar panel
    await async_register_panel(hass, entry)
    
    # Register services
    await async_setup_services(hass, coordinator)
    
    _LOGGER.info("Smart Heating integration setup complete")
    
    return True


async def async_register_panel(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the frontend panel.
    
    Args:
        hass: Home Assistant instance
        entry: Config entry
    """
    from homeassistant.components.frontend import async_register_built_in_panel
    
    # Register panel (this is a sync function despite the name)
    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Smart Heating",
        sidebar_icon="mdi:radiator",
        frontend_url_path="smart_heating",
        config={"url": "/smart_heating_ui"},
        require_admin=False,
    )
    
    _LOGGER.info("Smart Heating panel registered in sidebar")


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
    
    async def async_handle_add_device(call: ServiceCall) -> None:
        """Handle the add_device_to_area service call."""
        area_id = call.data[ATTR_AREA_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        device_type = call.data[ATTR_DEVICE_TYPE]
        
        _LOGGER.debug("Adding device %s (type: %s) to area %s", device_id, device_type, area_id)
        
        try:
            area_manager.add_device_to_area(area_id, device_id, device_type)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added device %s to area %s", device_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to add device: %s", err)
    
    async def async_handle_remove_device(call: ServiceCall) -> None:
        """Handle the remove_device_from_area service call."""
        area_id = call.data[ATTR_AREA_ID]
        device_id = call.data[ATTR_DEVICE_ID]
        
        _LOGGER.debug("Removing device %s from area %s", device_id, area_id)
        
        try:
            area_manager.remove_device_from_area(area_id, device_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed device %s from area %s", device_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove device: %s", err)
    
    async def async_handle_set_temperature(call: ServiceCall) -> None:
        """Handle the set_area_temperature service call."""
        area_id = call.data[ATTR_AREA_ID]
        temperature = call.data[ATTR_TEMPERATURE]
        
        _LOGGER.debug("Setting area %s temperature to %.1f°C", area_id, temperature)
        
        try:
            area_manager.set_area_target_temperature(area_id, temperature)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set area %s temperature to %.1f°C", area_id, temperature)
        except ValueError as err:
            _LOGGER.error("Failed to set temperature: %s", err)
    
    async def async_handle_enable_area(call: ServiceCall) -> None:
        """Handle the enable_area service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Enabling area %s", area_id)
        
        try:
            area_manager.enable_area(area_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Enabled area %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to enable area: %s", err)
    
    async def async_handle_disable_area(call: ServiceCall) -> None:
        """Handle the disable_area service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Disabling area %s", area_id)
        
        try:
            area_manager.disable_area(area_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Disabled area %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to disable area: %s", err)
    
    async def async_handle_add_schedule(call: ServiceCall) -> None:
        """Handle the add_schedule service call."""
        area_id = call.data[ATTR_AREA_ID]
        schedule_id = call.data[ATTR_SCHEDULE_ID]
        time_str = call.data[ATTR_TIME]
        temperature = call.data[ATTR_TEMPERATURE]
        days = call.data.get(ATTR_DAYS)
        
        _LOGGER.debug("Adding schedule %s to area %s: %s @ %.1f°C", 
                     schedule_id, area_id, time_str, temperature)
        
        try:
            area_manager.add_schedule_to_area(area_id, schedule_id, time_str, temperature, days)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added schedule %s to area %s", schedule_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to add schedule: %s", err)
    
    async def async_handle_remove_schedule(call: ServiceCall) -> None:
        """Handle the remove_schedule service call."""
        area_id = call.data[ATTR_AREA_ID]
        schedule_id = call.data[ATTR_SCHEDULE_ID]
        
        _LOGGER.debug("Removing schedule %s from area %s", schedule_id, area_id)
        
        try:
            area_manager.remove_schedule_from_area(area_id, schedule_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed schedule %s from area %s", schedule_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove schedule: %s", err)
    
    async def async_handle_enable_schedule(call: ServiceCall) -> None:
        """Handle the enable_schedule service call."""
        area_id = call.data[ATTR_AREA_ID]
        schedule_id = call.data[ATTR_SCHEDULE_ID]
        
        _LOGGER.debug("Enabling schedule %s in area %s", schedule_id, area_id)
        
        try:
            area = area_manager.get_area(area_id)
            if area and schedule_id in area.schedules:
                area.schedules[schedule_id].enabled = True
                await area_manager.async_save()
                await coordinator.async_request_refresh()
                _LOGGER.info("Enabled schedule %s in area %s", schedule_id, area_id)
            else:
                raise ValueError(f"Schedule {schedule_id} not found in area {area_id}")
        except ValueError as err:
            _LOGGER.error("Failed to enable schedule: %s", err)
    
    async def async_handle_disable_schedule(call: ServiceCall) -> None:
        """Handle the disable_schedule service call."""
        area_id = call.data[ATTR_AREA_ID]
        schedule_id = call.data[ATTR_SCHEDULE_ID]
        
        _LOGGER.debug("Disabling schedule %s in area %s", schedule_id, area_id)
        
        try:
            area = area_manager.get_area(area_id)
            if area and schedule_id in area.schedules:
                area.schedules[schedule_id].enabled = False
                await area_manager.async_save()
                await coordinator.async_request_refresh()
                _LOGGER.info("Disabled schedule %s in area %s", schedule_id, area_id)
            else:
                raise ValueError(f"Schedule {schedule_id} not found in area {area_id}")
        except ValueError as err:
            _LOGGER.error("Failed to disable schedule: %s", err)
    
    async def async_handle_set_night_boost(call: ServiceCall) -> None:
        """Handle the set_night_boost service call."""
        area_id = call.data[ATTR_AREA_ID]
        enabled = call.data.get(ATTR_NIGHT_BOOST_ENABLED)
        offset = call.data.get(ATTR_NIGHT_BOOST_OFFSET)
        
        _LOGGER.debug("Setting night boost for area %s: enabled=%s, offset=%s", 
                     area_id, enabled, offset)
        
        try:
            area = area_manager.get_area(area_id)
            if area is None:
                raise ValueError(f"Area {area_id} does not exist")
            
            if enabled is not None:
                area.night_boost_enabled = enabled
            if offset is not None:
                area.night_boost_offset = offset
            
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Updated night boost for area %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to set night boost: %s", err)
    
    async def async_handle_set_hysteresis(call: ServiceCall) -> None:
        """Handle the set_hysteresis service call."""
        hysteresis = call.data[ATTR_HYSTERESIS]
        
        _LOGGER.debug("Setting global hysteresis to %.2f°C", hysteresis)
        
        try:
            climate_controller = hass.data[DOMAIN].get("climate_controller")
            if climate_controller:
                climate_controller._hysteresis = hysteresis
                _LOGGER.info("Set global hysteresis to %.2f°C", hysteresis)
            else:
                raise ValueError("Climate controller not found")
        except ValueError as err:
            _LOGGER.error("Failed to set hysteresis: %s", err)
    
    # Service schemas
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
    
    ADD_SCHEDULE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_SCHEDULE_ID): cv.string,
        vol.Required(ATTR_TIME): cv.string,
        vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
        vol.Optional(ATTR_DAYS): vol.All(cv.ensure_list, [cv.string]),
    })
    
    REMOVE_SCHEDULE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_SCHEDULE_ID): cv.string,
    })
    
    SCHEDULE_CONTROL_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_SCHEDULE_ID): cv.string,
    })
    
    NIGHT_BOOST_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Optional(ATTR_NIGHT_BOOST_ENABLED): cv.boolean,
        vol.Optional(ATTR_NIGHT_BOOST_OFFSET): vol.Coerce(float),
    })
    
    HYSTERESIS_SCHEMA = vol.Schema({
        vol.Required(ATTR_HYSTERESIS): vol.Coerce(float),
    })
    
    # Register all services
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, async_handle_refresh)
    hass.services.async_register(DOMAIN, SERVICE_ADD_DEVICE_TO_AREA, async_handle_add_device, schema=ADD_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_AREA, async_handle_remove_device, schema=REMOVE_DEVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_AREA_TEMPERATURE, async_handle_set_temperature, schema=SET_TEMPERATURE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_AREA, async_handle_enable_area, schema=ZONE_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_AREA, async_handle_disable_area, schema=ZONE_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_SCHEDULE, async_handle_add_schedule, schema=ADD_SCHEDULE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_SCHEDULE, async_handle_remove_schedule, schema=REMOVE_SCHEDULE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_SCHEDULE, async_handle_enable_schedule, schema=SCHEDULE_CONTROL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_SCHEDULE, async_handle_disable_schedule, schema=SCHEDULE_CONTROL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_NIGHT_BOOST, async_handle_set_night_boost, schema=NIGHT_BOOST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_HYSTERESIS, async_handle_set_hysteresis, schema=HYSTERESIS_SCHEMA)
    
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
        # Stop climate controller
        if "climate_unsub" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["climate_unsub"]()
            _LOGGER.debug("Climate controller stopped")
        
        # Stop schedule executor
        if "schedule_executor" in hass.data[DOMAIN]:
            await hass.data[DOMAIN]["schedule_executor"].async_stop()
            _LOGGER.debug("Schedule executor stopped")
        
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
            hass.services.async_remove(DOMAIN, SERVICE_ADD_DEVICE_TO_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_DEVICE_FROM_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_SET_AREA_TEMPERATURE)
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_AREA)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_SCHEDULE)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_SCHEDULE)
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_SCHEDULE)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_SCHEDULE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_NIGHT_BOOST)
            hass.services.async_remove(DOMAIN, SERVICE_SET_HYSTERESIS)
            _LOGGER.debug("Smart Heating services removed")
    
    _LOGGER.info("Smart Heating integration unloaded")
    
    return unload_ok
