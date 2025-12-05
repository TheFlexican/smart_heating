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
    ATTR_NIGHT_BOOST_START_TIME,
    ATTR_NIGHT_BOOST_END_TIME,
    ATTR_HYSTERESIS,
    ATTR_OPENTHERM_GATEWAY,
    ATTR_OPENTHERM_ENABLED,
    ATTR_TRV_HEATING_TEMP,
    ATTR_TRV_IDLE_TEMP,
    ATTR_TRV_TEMP_OFFSET,
    ATTR_PRESET_MODE,
    ATTR_BOOST_DURATION,
    ATTR_BOOST_TEMP,
    ATTR_FROST_PROTECTION_ENABLED,
    ATTR_FROST_PROTECTION_TEMP,
    ATTR_HVAC_MODE,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_VALVE,
    DEVICE_TYPE_SWITCH,
    DOMAIN,
    PLATFORMS,
    PRESET_MODES,
    HVAC_MODES,
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
    SERVICE_SET_OPENTHERM_GATEWAY,
    SERVICE_SET_TRV_TEMPERATURES,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_BOOST_MODE,
    SERVICE_CANCEL_BOOST,
    SERVICE_SET_FROST_PROTECTION,
    SERVICE_ADD_WINDOW_SENSOR,
    SERVICE_REMOVE_WINDOW_SENSOR,
    SERVICE_ADD_PRESENCE_SENSOR,
    SERVICE_REMOVE_PRESENCE_SENSOR,
    SERVICE_SET_HVAC_MODE,
    SERVICE_COPY_SCHEDULE,
)
from .coordinator import SmartHeatingCoordinator
from .area_manager import AreaManager
from .api import setup_api
from .websocket import setup_websocket
from .climate_controller import ClimateController
from .scheduler import ScheduleExecutor
from .history import HistoryTracker
from .learning_engine import LearningEngine

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
    
    # Apply config entry options to area manager
    if entry.options:
        _LOGGER.debug("Loading config entry options: %s", entry.options)
        if entry.options.get("opentherm_gateway_id"):
            area_manager.set_opentherm_gateway(
                entry.options["opentherm_gateway_id"],
                enabled=entry.options.get("opentherm_enabled", True)
            )
            _LOGGER.info(
                "Applied OpenTherm config from options: %s (enabled: %s)",
                entry.options["opentherm_gateway_id"],
                entry.options.get("opentherm_enabled", True)
            )
    
    # Create history tracker
    history_tracker = HistoryTracker(hass)
    await history_tracker.async_load()
    hass.data[DOMAIN]["history"] = history_tracker
    
    # Create learning engine
    learning_engine = LearningEngine(hass)
    hass.data[DOMAIN]["learning_engine"] = learning_engine
    _LOGGER.info("Learning engine initialized")
    
    # Create coordinator instance
    coordinator = SmartHeatingCoordinator(hass, area_manager)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    _LOGGER.debug("Smart Heating coordinator stored in hass.data")
    
    # Create and start climate controller
    climate_controller = ClimateController(hass, area_manager, learning_engine)
    
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
    schedule_executor = ScheduleExecutor(hass, area_manager, learning_engine)
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
    from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
    
    # Remove panel if it already exists (from previous failed setup)
    try:
        async_remove_panel(hass, "smart_heating")  # Not actually async despite the name
        _LOGGER.debug("Removed existing Smart Heating panel")
    except (KeyError, ValueError):
        # Panel doesn't exist, that's fine
        pass
    
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
        start_time = call.data.get(ATTR_NIGHT_BOOST_START_TIME)
        end_time = call.data.get(ATTR_NIGHT_BOOST_END_TIME)
        smart_enabled = call.data.get("smart_night_boost_enabled")
        smart_target_time = call.data.get("smart_night_boost_target_time")
        weather_entity_id = call.data.get("weather_entity_id")
        
        _LOGGER.debug("Setting night boost for area %s: enabled=%s, offset=%s, start=%s, end=%s, smart=%s", 
                     area_id, enabled, offset, start_time, end_time, smart_enabled)
        
        try:
            area = area_manager.get_area(area_id)
            if area is None:
                raise ValueError(f"Area {area_id} does not exist")
            
            # Manual night boost settings
            if enabled is not None:
                area.night_boost_enabled = enabled
            if offset is not None:
                area.night_boost_offset = offset
            if start_time is not None:
                area.night_boost_start_time = start_time
            if end_time is not None:
                area.night_boost_end_time = end_time
            
            # Smart night boost settings
            if smart_enabled is not None:
                area.smart_night_boost_enabled = smart_enabled
            if smart_target_time is not None:
                area.smart_night_boost_target_time = smart_target_time
            if weather_entity_id is not None:
                area.weather_entity_id = weather_entity_id
            
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
    
    async def async_handle_set_opentherm_gateway(call: ServiceCall) -> None:
        """Handle the set_opentherm_gateway service call."""
        gateway_id = call.data.get("gateway_id")
        enabled = call.data.get("enabled", True)
        
        _LOGGER.debug("Setting OpenTherm gateway to %s (enabled: %s)", gateway_id, enabled)
        
        try:
            area_manager.set_opentherm_gateway(gateway_id, enabled)
            await area_manager.async_save()
            _LOGGER.info("Set OpenTherm gateway to %s (enabled: %s)", gateway_id, enabled)
        except ValueError as err:
            _LOGGER.error("Failed to set OpenTherm gateway: %s", err)
    
    async def async_handle_set_trv_temperatures(call: ServiceCall) -> None:
        """Handle the set_trv_temperatures service call."""
        heating_temp = call.data.get("heating_temp", 25.0)
        idle_temp = call.data.get("idle_temp", 10.0)
        temp_offset = call.data.get("temp_offset")
        
        if temp_offset is not None:
            _LOGGER.debug(
                "Setting TRV temperatures: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
                heating_temp, idle_temp, temp_offset
            )
        else:
            _LOGGER.debug("Setting TRV temperatures: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp)
        
        try:
            area_manager.set_trv_temperatures(heating_temp, idle_temp, temp_offset)
            await area_manager.async_save()
            if temp_offset is not None:
                _LOGGER.info(
                    "Set TRV temperatures: heating=%.1f°C, idle=%.1f°C, offset=%.1f°C",
                    heating_temp, idle_temp, temp_offset
                )
            else:
                _LOGGER.info("Set TRV temperatures: heating=%.1f°C, idle=%.1f°C", heating_temp, idle_temp)
        except ValueError as err:
            _LOGGER.error("Failed to set TRV temperatures: %s", err)
    
    async def async_handle_set_preset_mode(call: ServiceCall) -> None:
        """Handle the set_preset_mode service call."""
        area_id = call.data[ATTR_AREA_ID]
        preset_mode = call.data[ATTR_PRESET_MODE]
        
        _LOGGER.debug("Setting preset mode for area %s to %s", area_id, preset_mode)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.set_preset_mode(preset_mode)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set preset mode for area %s to %s", area_id, preset_mode)
        except ValueError as err:
            _LOGGER.error("Failed to set preset mode: %s", err)
    
    async def async_handle_set_boost_mode(call: ServiceCall) -> None:
        """Handle the set_boost_mode service call."""
        area_id = call.data[ATTR_AREA_ID]
        duration = call.data.get(ATTR_BOOST_DURATION, 60)
        temp = call.data.get(ATTR_BOOST_TEMP)
        
        _LOGGER.debug("Setting boost mode for area %s: %d minutes", area_id, duration)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.set_boost_mode(duration, temp)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Activated boost mode for area %s: %d minutes at %.1f°C", 
                        area_id, duration, area.boost_temp)
        except ValueError as err:
            _LOGGER.error("Failed to set boost mode: %s", err)
    
    async def async_handle_cancel_boost(call: ServiceCall) -> None:
        """Handle the cancel_boost service call."""
        area_id = call.data[ATTR_AREA_ID]
        
        _LOGGER.debug("Cancelling boost mode for area %s", area_id)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.cancel_boost_mode()
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Cancelled boost mode for area %s", area_id)
        except ValueError as err:
            _LOGGER.error("Failed to cancel boost mode: %s", err)
    
    async def async_handle_set_frost_protection(call: ServiceCall) -> None:
        """Handle the set_frost_protection service call."""
        enabled = call.data.get(ATTR_FROST_PROTECTION_ENABLED)
        temp = call.data.get(ATTR_FROST_PROTECTION_TEMP)
        
        _LOGGER.debug("Setting frost protection: enabled=%s, temp=%.1f°C", enabled, temp if temp else 7.0)
        
        try:
            if enabled is not None:
                area_manager.frost_protection_enabled = enabled
            if temp is not None:
                area_manager.frost_protection_temp = temp
            
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set frost protection: enabled=%s, temp=%.1f°C", 
                        area_manager.frost_protection_enabled,
                        area_manager.frost_protection_temp)
        except ValueError as err:
            _LOGGER.error("Failed to set frost protection: %s", err)
    
    async def async_handle_add_window_sensor(call: ServiceCall) -> None:
        """Handle the add_window_sensor service call."""
        area_id = call.data[ATTR_AREA_ID]
        entity_id = call.data["entity_id"]
        
        _LOGGER.debug("Adding window sensor %s to area %s", entity_id, area_id)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.add_window_sensor(entity_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added window sensor %s to area %s", entity_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to add window sensor: %s", err)
    
    async def async_handle_remove_window_sensor(call: ServiceCall) -> None:
        """Handle the remove_window_sensor service call."""
        area_id = call.data[ATTR_AREA_ID]
        entity_id = call.data["entity_id"]
        
        _LOGGER.debug("Removing window sensor %s from area %s", entity_id, area_id)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.remove_window_sensor(entity_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed window sensor %s from area %s", entity_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove window sensor: %s", err)
    
    async def async_handle_add_presence_sensor(call: ServiceCall) -> None:
        """Handle the add_presence_sensor service call."""
        area_id = call.data[ATTR_AREA_ID]
        entity_id = call.data["entity_id"]
        
        _LOGGER.debug("Adding presence sensor %s to area %s", entity_id, area_id)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.add_presence_sensor(entity_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Added presence sensor %s to area %s", entity_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to add presence sensor: %s", err)
    
    async def async_handle_remove_presence_sensor(call: ServiceCall) -> None:
        """Handle the remove_presence_sensor service call."""
        area_id = call.data[ATTR_AREA_ID]
        entity_id = call.data["entity_id"]
        
        _LOGGER.debug("Removing presence sensor %s from area %s", entity_id, area_id)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.remove_presence_sensor(entity_id)
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed presence sensor %s from area %s", entity_id, area_id)
        except ValueError as err:
            _LOGGER.error("Failed to remove presence sensor: %s", err)
    
    async def async_handle_set_hvac_mode(call: ServiceCall) -> None:
        """Handle the set_hvac_mode service call."""
        area_id = call.data[ATTR_AREA_ID]
        hvac_mode = call.data[ATTR_HVAC_MODE]
        
        _LOGGER.debug("Setting HVAC mode for area %s to %s", area_id, hvac_mode)
        
        area = area_manager.get_area(area_id)
        if not area:
            _LOGGER.error("Area %s not found", area_id)
            return
        
        try:
            area.hvac_mode = hvac_mode
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Set HVAC mode for area %s to %s", area_id, hvac_mode)
        except ValueError as err:
            _LOGGER.error("Failed to set HVAC mode: %s", err)
    
    async def async_handle_copy_schedule(call: ServiceCall) -> None:
        """Handle the copy_schedule service call."""
        source_area_id = call.data["source_area_id"]
        source_schedule_id = call.data["source_schedule_id"]
        target_area_id = call.data["target_area_id"]
        target_days = call.data.get("target_days", [])
        
        _LOGGER.debug("Copying schedule %s from area %s to area %s", 
                     source_schedule_id, source_area_id, target_area_id)
        
        source_area = area_manager.get_area(source_area_id)
        target_area = area_manager.get_area(target_area_id)
        
        if not source_area:
            _LOGGER.error("Source area %s not found", source_area_id)
            return
        if not target_area:
            _LOGGER.error("Target area %s not found", target_area_id)
            return
        
        try:
            from .area_manager import Schedule
            import uuid
            
            source_schedule = source_area.schedules.get(source_schedule_id)
            if not source_schedule:
                _LOGGER.error("Schedule %s not found in area %s", source_schedule_id, source_area_id)
                return
            
            # Create new schedule(s) for target days
            if target_days:
                for day in target_days:
                    new_schedule = Schedule(
                        schedule_id=f"{day.lower()}_{uuid.uuid4().hex[:8]}",
                        time=source_schedule.start_time,
                        temperature=source_schedule.temperature,
                        day=day,
                        start_time=source_schedule.start_time,
                        end_time=source_schedule.end_time,
                        enabled=source_schedule.enabled
                    )
                    target_area.add_schedule(new_schedule)
            else:
                # Copy with same days
                new_schedule = Schedule(
                    schedule_id=f"copied_{uuid.uuid4().hex[:8]}",
                    time=source_schedule.start_time,
                    temperature=source_schedule.temperature,
                    day=source_schedule.day,
                    start_time=source_schedule.start_time,
                    end_time=source_schedule.end_time,
                    enabled=source_schedule.enabled
                )
                target_area.add_schedule(new_schedule)
            
            await area_manager.async_save()
            await coordinator.async_request_refresh()
            _LOGGER.info("Copied schedule from area %s to area %s", source_area_id, target_area_id)
        except Exception as err:
            _LOGGER.error("Failed to copy schedule: %s", err)
    
    # Service schemas
    ADD_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_DEVICE_TYPE): vol.In([
            DEVICE_TYPE_THERMOSTAT,
            DEVICE_TYPE_TEMPERATURE_SENSOR,
            DEVICE_TYPE_OPENTHERM_GATEWAY,
            DEVICE_TYPE_VALVE,
            DEVICE_TYPE_SWITCH,
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
        vol.Optional(ATTR_NIGHT_BOOST_START_TIME): cv.string,
        vol.Optional(ATTR_NIGHT_BOOST_END_TIME): cv.string,
        vol.Optional("smart_night_boost_enabled"): cv.boolean,
        vol.Optional("smart_night_boost_target_time"): cv.string,
        vol.Optional("weather_entity_id"): cv.string,
    })
    
    HYSTERESIS_SCHEMA = vol.Schema({
        vol.Required(ATTR_HYSTERESIS): vol.Coerce(float),
    })
    
    OPENTHERM_GATEWAY_SCHEMA = vol.Schema({
        vol.Optional("gateway_id"): cv.string,
        vol.Optional("enabled", default=True): cv.boolean,
    })
    
    TRV_TEMPERATURES_SCHEMA = vol.Schema({
        vol.Optional("heating_temp", default=25.0): vol.Coerce(float),
        vol.Optional("idle_temp", default=10.0): vol.Coerce(float),
        vol.Optional("temp_offset"): vol.Coerce(float),
    })
    
    PRESET_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_PRESET_MODE): vol.In(PRESET_MODES),
    })
    
    BOOST_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Optional(ATTR_BOOST_DURATION, default=60): vol.Coerce(int),
        vol.Optional(ATTR_BOOST_TEMP): vol.Coerce(float),
    })
    
    CANCEL_BOOST_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
    })
    
    FROST_PROTECTION_SCHEMA = vol.Schema({
        vol.Optional(ATTR_FROST_PROTECTION_ENABLED): cv.boolean,
        vol.Optional(ATTR_FROST_PROTECTION_TEMP): vol.Coerce(float),
    })
    
    WINDOW_SENSOR_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required("entity_id"): cv.entity_id,
    })
    
    PRESENCE_SENSOR_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required("entity_id"): cv.entity_id,
    })
    
    HVAC_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_AREA_ID): cv.string,
        vol.Required(ATTR_HVAC_MODE): vol.In(HVAC_MODES),
    })
    
    COPY_SCHEDULE_SCHEMA = vol.Schema({
        vol.Required("source_area_id"): cv.string,
        vol.Required("source_schedule_id"): cv.string,
        vol.Required("target_area_id"): cv.string,
        vol.Optional("target_days"): vol.All(cv.ensure_list, [cv.string]),
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
    hass.services.async_register(DOMAIN, SERVICE_SET_OPENTHERM_GATEWAY, async_handle_set_opentherm_gateway, schema=OPENTHERM_GATEWAY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_TRV_TEMPERATURES, async_handle_set_trv_temperatures, schema=TRV_TEMPERATURES_SCHEMA)
    # New services
    hass.services.async_register(DOMAIN, SERVICE_SET_PRESET_MODE, async_handle_set_preset_mode, schema=PRESET_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_BOOST_MODE, async_handle_set_boost_mode, schema=BOOST_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CANCEL_BOOST, async_handle_cancel_boost, schema=CANCEL_BOOST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_FROST_PROTECTION, async_handle_set_frost_protection, schema=FROST_PROTECTION_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_WINDOW_SENSOR, async_handle_add_window_sensor, schema=WINDOW_SENSOR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_WINDOW_SENSOR, async_handle_remove_window_sensor, schema=WINDOW_SENSOR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_PRESENCE_SENSOR, async_handle_add_presence_sensor, schema=PRESENCE_SENSOR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_PRESENCE_SENSOR, async_handle_remove_presence_sensor, schema=PRESENCE_SENSOR_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_HVAC_MODE, async_handle_set_hvac_mode, schema=HVAC_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_COPY_SCHEDULE, async_handle_copy_schedule, schema=COPY_SCHEDULE_SCHEMA)
    
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
            from homeassistant.components.frontend import async_remove_panel
            async_remove_panel(hass, "smart_heating")  # Not actually async despite the name
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
            hass.services.async_remove(DOMAIN, SERVICE_SET_OPENTHERM_GATEWAY)
            hass.services.async_remove(DOMAIN, SERVICE_SET_TRV_TEMPERATURES)
            # Remove new services
            hass.services.async_remove(DOMAIN, SERVICE_SET_PRESET_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_BOOST_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_CANCEL_BOOST)
            hass.services.async_remove(DOMAIN, SERVICE_SET_FROST_PROTECTION)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_WINDOW_SENSOR)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_WINDOW_SENSOR)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_PRESENCE_SENSOR)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_PRESENCE_SENSOR)
            hass.services.async_remove(DOMAIN, SERVICE_SET_HVAC_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_COPY_SCHEDULE)
            _LOGGER.debug("Smart Heating services removed")
    
    _LOGGER.info("Smart Heating integration unloaded")
    
    return unload_ok
