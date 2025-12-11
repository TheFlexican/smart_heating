"""The Smart Heating integration."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .api import setup_api
from .advanced_metrics_collector import AdvancedMetricsCollector
from .area_logger import AreaLogger
from .area_manager import AreaManager
from .climate_controller import ClimateController
from .comparison_engine import ComparisonEngine
from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_DEVICE_TO_AREA,
    SERVICE_ADD_PRESENCE_SENSOR,
    SERVICE_ADD_SCHEDULE,
    SERVICE_ADD_WINDOW_SENSOR,
    SERVICE_CANCEL_BOOST,
    SERVICE_COPY_SCHEDULE,
    SERVICE_DISABLE_AREA,
    SERVICE_DISABLE_SCHEDULE,
    SERVICE_DISABLE_VACATION_MODE,
    SERVICE_ENABLE_AREA,
    SERVICE_ENABLE_SCHEDULE,
    SERVICE_ENABLE_VACATION_MODE,
    SERVICE_REFRESH,
    SERVICE_REMOVE_DEVICE_FROM_AREA,
    SERVICE_REMOVE_PRESENCE_SENSOR,
    SERVICE_REMOVE_SAFETY_SENSOR,
    SERVICE_REMOVE_SCHEDULE,
    SERVICE_REMOVE_WINDOW_SENSOR,
    SERVICE_SET_AREA_TEMPERATURE,
    SERVICE_SET_BOOST_MODE,
    SERVICE_SET_FROST_PROTECTION,
    SERVICE_SET_HISTORY_RETENTION,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_HYSTERESIS,
    SERVICE_SET_NIGHT_BOOST,
    SERVICE_SET_OPENTHERM_GATEWAY,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_SAFETY_SENSOR,
    SERVICE_SET_TRV_TEMPERATURES,
)
from .coordinator import SmartHeatingCoordinator
from .efficiency_calculator import EfficiencyCalculator
from .history import HistoryTracker
from .learning_engine import LearningEngine
from .opentherm_logger import OpenThermLogger
from .safety_monitor import SafetyMonitor
from .scheduler import ScheduleExecutor
from .user_manager import UserManager
from .vacation_manager import VacationManager
from .websocket import setup_websocket

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
            # Only override saved numeric gateway IDs if options explicitly provide
            # a string gateway id and there's no numeric stored value. If a
            # numeric gateway ID is stored (legacy style), prefer the stored value.
            existing_id = getattr(area_manager, "opentherm_gateway_id", None)
            if existing_id and isinstance(existing_id, str) and existing_id.isnumeric():
                _LOGGER.debug(
                    "Skipping options override for OpenTherm gateway: numeric value present"
                )
            else:
                await area_manager.set_opentherm_gateway(
                    entry.options["opentherm_gateway_id"]
                )
            _LOGGER.info(
                "Applied OpenTherm config from options: %s",
                entry.options["opentherm_gateway_id"],
            )

    # Store area_manager in hass.data for other components
    hass.data[DOMAIN]["area_manager"] = area_manager

    # Create history tracker
    history_tracker = HistoryTracker(hass)
    await history_tracker.async_load()
    hass.data[DOMAIN]["history"] = history_tracker

    # Create area logger for development logging
    # Store logs in .storage/smart_heating/logs/{area_id}/{event_type}.jsonl
    storage_path = hass.config.path(".storage", DOMAIN)
    area_logger = AreaLogger(storage_path, hass)
    hass.data[DOMAIN]["area_logger"] = area_logger
    _LOGGER.info("Area logger initialized at %s", storage_path)

    # Create OpenTherm logger for gateway monitoring
    opentherm_logger = OpenThermLogger(hass)
    hass.data[DOMAIN]["opentherm_logger"] = opentherm_logger
    _LOGGER.info("OpenTherm logger initialized")

    # Create vacation manager
    vacation_manager = VacationManager(hass, storage_path)
    await vacation_manager.async_load()
    hass.data[DOMAIN]["vacation_manager"] = vacation_manager
    _LOGGER.info("Vacation manager initialized")

    # Create user manager
    user_manager = UserManager(hass, storage_path)
    await user_manager.async_load()
    hass.data[DOMAIN]["user_manager"] = user_manager
    _LOGGER.info("User manager initialized")

    # Create efficiency calculator
    efficiency_calculator = EfficiencyCalculator(hass, history_tracker)
    hass.data[DOMAIN]["efficiency_calculator"] = efficiency_calculator
    _LOGGER.info("Efficiency calculator initialized")

    # Create comparison engine
    comparison_engine = ComparisonEngine(hass, efficiency_calculator)
    hass.data[DOMAIN]["comparison_engine"] = comparison_engine
    _LOGGER.info("Comparison engine initialized")

    # Create advanced metrics collector
    advanced_metrics_collector = AdvancedMetricsCollector(hass)
    hass.data[DOMAIN]["advanced_metrics_collector"] = advanced_metrics_collector
    # Setup will run async, logs if database not available
    hass.async_create_task(advanced_metrics_collector.async_setup())
    _LOGGER.info("Advanced metrics collector initialized")

    # Create safety monitor
    safety_monitor = SafetyMonitor(hass, area_manager)
    await safety_monitor.async_setup()
    hass.data[DOMAIN]["safety_monitor"] = safety_monitor
    _LOGGER.info("Safety monitor initialized")

    # Create learning engine
    learning_engine = LearningEngine(hass)
    await learning_engine.async_setup()
    hass.data[DOMAIN]["learning_engine"] = learning_engine
    _LOGGER.info("Learning engine initialized")

    # Create config manager for import/export
    from .config_manager import ConfigManager

    config_manager = ConfigManager(hass, area_manager, storage_path)
    hass.data[DOMAIN]["config_manager"] = config_manager
    _LOGGER.info("Config manager initialized")

    # Create coordinator instance
    coordinator = SmartHeatingCoordinator(hass, entry, area_manager)

    # Set up state change listeners before first refresh
    await coordinator.async_setup()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.debug("Smart Heating coordinator stored in hass.data")

    # Create and start climate controller
    climate_controller = ClimateController(hass, area_manager, learning_engine)

    # Initialize handlers with area_logger
    climate_controller.set_area_logger(area_logger)

    # Store climate controller
    hass.data[DOMAIN]["climate_controller"] = climate_controller

    # Set up periodic heating control (every 30 seconds)
    async def async_control_heating_wrapper(now):
        """Wrapper for periodic climate control."""
        try:
            await climate_controller.async_control_heating()
        except Exception as err:
            _LOGGER.error("Error in climate control: %s", err, exc_info=True)

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

    # Pass area_logger to schedule executor
    schedule_executor.area_logger = area_logger

    hass.data[DOMAIN]["schedule_executor"] = schedule_executor
    await schedule_executor.async_start()
    _LOGGER.info("Schedule executor started")

    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up REST API and WebSocket
    await setup_api(hass, area_manager)
    await setup_websocket(hass)

    # Discover OpenTherm Gateway capabilities if configured
    if area_manager.opentherm_gateway_id:

        async def discover_capabilities():
            await asyncio.sleep(10)  # Wait for HA to be fully started
            try:
                await opentherm_logger.async_discover_mqtt_capabilities(
                    area_manager.opentherm_gateway_id
                )
            except Exception as err:
                _LOGGER.error("Failed to discover OpenTherm capabilities: %s", err)

        hass.async_create_task(discover_capabilities())

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
    from homeassistant.components.frontend import (
        async_register_built_in_panel,
        async_remove_panel,
    )

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


async def async_setup_services(
    hass: HomeAssistant, coordinator: SmartHeatingCoordinator
) -> None:
    """Set up services for Smart Heating.

    Args:
        hass: Home Assistant instance
        coordinator: Data coordinator instance
    """
    from functools import partial

    from .ha_services import (
        # Schemas
        ADD_DEVICE_SCHEMA,
        ADD_SCHEDULE_SCHEMA,
        BOOST_MODE_SCHEMA,
        CANCEL_BOOST_SCHEMA,
        COPY_SCHEDULE_SCHEMA,
        FROST_PROTECTION_SCHEMA,
        HISTORY_RETENTION_SCHEMA,
        HVAC_MODE_SCHEMA,
        HYSTERESIS_SCHEMA,
        NIGHT_BOOST_SCHEMA,
        OPENTHERM_GATEWAY_SCHEMA,
        PRESENCE_SENSOR_SCHEMA,
        PRESET_MODE_SCHEMA,
        REMOVE_DEVICE_SCHEMA,
        REMOVE_SCHEDULE_SCHEMA,
        SAFETY_SENSOR_SCHEMA,
        SCHEDULE_CONTROL_SCHEMA,
        SET_TEMPERATURE_SCHEMA,
        TRV_TEMPERATURES_SCHEMA,
        VACATION_MODE_SCHEMA,
        WINDOW_SENSOR_SCHEMA,
        ZONE_ID_SCHEMA,
        async_handle_add_device,
        async_handle_add_presence_sensor,
        async_handle_add_schedule,
        async_handle_add_window_sensor,
        async_handle_cancel_boost,
        async_handle_copy_schedule,
        async_handle_disable_area,
        async_handle_disable_schedule,
        async_handle_disable_vacation_mode,
        async_handle_enable_area,
        async_handle_enable_schedule,
        async_handle_enable_vacation_mode,
        # Handlers
        async_handle_refresh,
        async_handle_remove_device,
        async_handle_remove_presence_sensor,
        async_handle_remove_safety_sensor,
        async_handle_remove_schedule,
        async_handle_remove_window_sensor,
        async_handle_set_boost_mode,
        async_handle_set_frost_protection,
        async_handle_set_history_retention,
        async_handle_set_hvac_mode,
        async_handle_set_hysteresis,
        async_handle_set_night_boost,
        async_handle_set_opentherm_gateway,
        async_handle_set_preset_mode,
        async_handle_set_safety_sensor,
        async_handle_set_temperature,
        async_handle_set_trv_temperatures,
    )

    area_manager = coordinator.area_manager

    # Register all services with partial functions to inject dependencies
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, partial(async_handle_refresh, coordinator=coordinator)
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_DEVICE_TO_AREA,
        partial(
            async_handle_add_device, area_manager=area_manager, coordinator=coordinator
        ),
        schema=ADD_DEVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_DEVICE_FROM_AREA,
        partial(
            async_handle_remove_device,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=REMOVE_DEVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AREA_TEMPERATURE,
        partial(
            async_handle_set_temperature,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=SET_TEMPERATURE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE_AREA,
        partial(
            async_handle_enable_area, area_manager=area_manager, coordinator=coordinator
        ),
        schema=ZONE_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE_AREA,
        partial(
            async_handle_disable_area,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=ZONE_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_SCHEDULE,
        partial(
            async_handle_add_schedule,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=ADD_SCHEDULE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_SCHEDULE,
        partial(
            async_handle_remove_schedule,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=REMOVE_SCHEDULE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE_SCHEDULE,
        partial(
            async_handle_enable_schedule,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=SCHEDULE_CONTROL_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE_SCHEDULE,
        partial(
            async_handle_disable_schedule,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=SCHEDULE_CONTROL_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_NIGHT_BOOST,
        partial(
            async_handle_set_night_boost,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=NIGHT_BOOST_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HYSTERESIS,
        partial(async_handle_set_hysteresis, hass=hass, coordinator=coordinator),
        schema=HYSTERESIS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_OPENTHERM_GATEWAY,
        partial(
            async_handle_set_opentherm_gateway,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=OPENTHERM_GATEWAY_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TRV_TEMPERATURES,
        partial(
            async_handle_set_trv_temperatures,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=TRV_TEMPERATURES_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        partial(
            async_handle_set_preset_mode,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=PRESET_MODE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BOOST_MODE,
        partial(
            async_handle_set_boost_mode,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=BOOST_MODE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_BOOST,
        partial(
            async_handle_cancel_boost,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=CANCEL_BOOST_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FROST_PROTECTION,
        partial(
            async_handle_set_frost_protection,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=FROST_PROTECTION_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_WINDOW_SENSOR,
        partial(
            async_handle_add_window_sensor,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=WINDOW_SENSOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_WINDOW_SENSOR,
        partial(
            async_handle_remove_window_sensor,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=WINDOW_SENSOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PRESENCE_SENSOR,
        partial(
            async_handle_add_presence_sensor,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=PRESENCE_SENSOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_PRESENCE_SENSOR,
        partial(
            async_handle_remove_presence_sensor,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=PRESENCE_SENSOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HVAC_MODE,
        partial(
            async_handle_set_hvac_mode,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=HVAC_MODE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_COPY_SCHEDULE,
        partial(
            async_handle_copy_schedule,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=COPY_SCHEDULE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HISTORY_RETENTION,
        partial(async_handle_set_history_retention, hass=hass, coordinator=coordinator),
        schema=HISTORY_RETENTION_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE_VACATION_MODE,
        partial(async_handle_enable_vacation_mode, hass=hass, coordinator=coordinator),
        schema=VACATION_MODE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE_VACATION_MODE,
        partial(async_handle_disable_vacation_mode, hass=hass, coordinator=coordinator),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SAFETY_SENSOR,
        partial(
            async_handle_set_safety_sensor,
            hass=hass,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
        schema=SAFETY_SENSOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_SAFETY_SENSOR,
        partial(
            async_handle_remove_safety_sensor,
            hass=hass,
            area_manager=area_manager,
            coordinator=coordinator,
        ),
    )

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
        # Shutdown safety monitor
        if "safety_monitor" in hass.data[DOMAIN]:
            await hass.data[DOMAIN]["safety_monitor"].async_shutdown()
            _LOGGER.debug("Safety monitor stopped")

        # Shutdown coordinator and remove state listeners
        if entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry.entry_id]
            await coordinator.async_shutdown()
            _LOGGER.debug("Coordinator state listeners removed")

        # Stop climate controller
        if "climate_unsub" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["climate_unsub"]()
            _LOGGER.debug("Climate controller stopped")

        # Stop schedule executor
        if "schedule_executor" in hass.data[DOMAIN]:
            await hass.data[DOMAIN]["schedule_executor"].async_stop()
            _LOGGER.debug("Schedule executor stopped")

        # Unload history tracker
        if "history" in hass.data[DOMAIN]:
            await hass.data[DOMAIN]["history"].async_unload()
            _LOGGER.debug("History tracker unloaded")

        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Smart Heating coordinator removed from hass.data")

        # Remove sidebar panel
        try:
            from homeassistant.components.frontend import async_remove_panel

            async_remove_panel(
                hass, "smart_heating"
            )  # Not actually async despite the name
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
            hass.services.async_remove(DOMAIN, SERVICE_SET_HISTORY_RETENTION)
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_VACATION_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_VACATION_MODE)
            hass.services.async_remove(DOMAIN, SERVICE_SET_SAFETY_SENSOR)
            hass.services.async_remove(DOMAIN, SERVICE_REMOVE_SAFETY_SENSOR)
            _LOGGER.debug("Smart Heating services removed")

    _LOGGER.info("Smart Heating integration unloaded")

    return unload_ok
