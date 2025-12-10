"""Area API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..models import Area
from ..utils import (
    build_area_response,
    build_device_info,
    get_coordinator,
    get_coordinator_devices,
)

_LOGGER = logging.getLogger(__name__)


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_areas(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Get all Home Assistant areas.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with HA areas
    """
    # Get Home Assistant's area registry
    area_registry = ar.async_get(hass)

    areas_data = []
    for area in area_registry.areas.values():
        area_id = area.id
        area_name = area.name

        # Check if we have stored data for this area
        stored_area = area_manager.get_area(area_id)

        if stored_area:
            # Build devices list with coordinator data
            devices_list = []
            coordinator_devices = get_coordinator_devices(hass, area_id)

            for dev_id, dev_data in stored_area.devices.items():
                state = hass.states.get(dev_id)
                coord_device = coordinator_devices.get(dev_id)
                devices_list.append(
                    build_device_info(dev_id, dev_data, state, coord_device)
                )

            # Build area response using utility
            area_response = build_area_response(stored_area, devices_list)
            # Override name with HA area name
            area_response["name"] = area_name
            areas_data.append(area_response)
        else:
            # Default data for HA area without stored settings
            areas_data.append(
                {
                    "id": area_id,
                    "name": area_name,
                    "enabled": True,
                    "hidden": False,
                    "state": "idle",
                    "target_temperature": 20.0,
                    "current_temperature": None,
                    "devices": [],
                    "schedules": [],
                    "manual_override": False,
                }
            )

    return web.json_response({"areas": areas_data})


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Get a specific area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response with area data
    """
    area = area_manager.get_area(area_id)

    if area is None:
        return web.json_response({"error": f"Zone {area_id} not found"}, status=404)

    # Build devices list
    devices_list = []
    for dev_id, dev_data in area.devices.items():
        state = hass.states.get(dev_id)
        devices_list.append(build_device_info(dev_id, dev_data, state))

    # Build area response using utility
    area_data = build_area_response(area, devices_list)

    return web.json_response(area_data)


async def handle_set_temperature(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set area temperature.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Temperature data

    Returns:
        JSON response
    """
    from ..utils import validate_area_id, validate_temperature

    # Validate area_id
    is_valid, error_msg = validate_area_id(area_id)
    if not is_valid:
        return web.json_response({"error": error_msg}, status=400)

    # Validate temperature
    temperature = data.get("temperature")
    is_valid, error_msg = validate_temperature(temperature)
    if not is_valid:
        return web.json_response({"error": error_msg}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        old_temp = area.target_temperature
        old_effective = area.get_effective_target_temperature()
        preset_context = (
            f", preset={area.preset_mode}" if area.preset_mode != "none" else ""
        )

        _LOGGER.warning(
            "🌡️ API: SET TEMPERATURE for %s: %.1f°C → %.1f°C%s | Effective: %.1f°C → ?",
            area.name,
            old_temp,
            temperature,
            preset_context,
            old_effective,
        )

        area_manager.set_area_target_temperature(area_id, temperature)

        # Clear manual override mode when user controls temperature via app
        if area and hasattr(area, "manual_override") and area.manual_override:
            _LOGGER.warning(
                "🔓 Clearing manual override for %s - app now in control", area.name
            )
            area.manual_override = False

        await area_manager.async_save()

        new_effective = area.get_effective_target_temperature()
        _LOGGER.warning(
            "✓ Temperature set: %s | Effective: %.1f°C → %.1f°C",
            area.name,
            old_effective,
            new_effective,
        )

        # Trigger immediate climate control
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()

        # Request coordinator refresh
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_enable_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Enable a area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response
    """
    try:
        area_manager.enable_area(area_id)
        await area_manager.async_save()

        # Check if this was the area that triggered a safety alert
        safety_monitor = hass.data.get(DOMAIN, {}).get("safety_monitor")
        if safety_monitor and area_manager.is_safety_alert_active():
            # If area being enabled, check if we should clear global safety alert
            area_manager.set_safety_alert_active(False)
            _LOGGER.info(
                "Safety alert cleared - area '%s' manually re-enabled", area_id
            )

        # Trigger immediate climate control
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_disable_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Disable a area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response
    """
    try:
        area_manager.disable_area(area_id)
        await area_manager.async_save()

        # Trigger immediate climate control to turn off devices
        climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_hide_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Hide an area from main view.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            # Area doesn't exist in storage yet - create it
            # Get area name from HA registry
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if not ha_area:
                return web.json_response(
                    {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                )

            # Create area with default settings
            area = Area(
                area_id=area_id,
                name=ha_area.name,
                target_temperature=20.0,
                enabled=True,
            )
            area.area_manager = area_manager
            area_manager.areas[area_id] = area

        area.hidden = True
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        return web.json_response({"error": str(err)}, status=500)


async def handle_unhide_area(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str
) -> web.Response:
    """Unhide an area to show in main view.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            # Area doesn't exist in storage yet - create it
            # Get area name from HA registry
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if not ha_area:
                return web.json_response(
                    {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                )

            # Create area with default settings
            area = Area(
                area_id=area_id,
                name=ha_area.name,
                target_temperature=20.0,
                enabled=True,
            )
            area.area_manager = area_manager
            area_manager.areas[area_id] = area

        area.hidden = False
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_switch_shutdown(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set whether switches/pumps should shutdown when area is not heating.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: {"shutdown": true/false}

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        shutdown = data.get("shutdown", True)
        area.shutdown_switches_when_idle = shutdown
        await area_manager.async_save()

        _LOGGER.info(
            "Area %s: shutdown_switches_when_idle set to %s", area_id, shutdown
        )

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting switch shutdown for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_area_hysteresis(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set area-specific hysteresis or use global setting.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: {"use_global": true/false, "hysteresis": float (optional)}

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        use_global = data.get("use_global", False)

        if use_global:
            # Use global hysteresis setting
            area.hysteresis_override = None
            _LOGGER.info(
                "Area %s: Setting hysteresis_override to None (global)", area_id
            )
        else:
            # Use area-specific hysteresis
            hysteresis = data.get("hysteresis")
            if hysteresis is None:
                return web.json_response(
                    {"error": "hysteresis value required when use_global is false"},
                    status=400,
                )

            # Validate range
            if hysteresis < 0.1 or hysteresis > 2.0:
                return web.json_response(
                    {"error": "Hysteresis must be between 0.1 and 2.0°C"}, status=400
                )

            area.hysteresis_override = float(hysteresis)
            _LOGGER.info(
                "Area %s: Setting hysteresis_override to %.1f°C", area_id, hysteresis
            )

        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting hysteresis for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_auto_preset(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set auto preset configuration for area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Auto preset data

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Update auto preset settings (support both 'enabled' and 'auto_preset_enabled')
        if "auto_preset_enabled" in data:
            area.auto_preset_enabled = bool(data["auto_preset_enabled"])
        elif "enabled" in data:
            area.auto_preset_enabled = bool(data["enabled"])

        # Update preset selections
        if "auto_preset_home" in data:
            area.auto_preset_home = str(data["auto_preset_home"])
        elif "home_preset" in data:
            area.auto_preset_home = str(data["home_preset"])

        if "auto_preset_away" in data:
            area.auto_preset_away = str(data["auto_preset_away"])
        elif "away_preset" in data:
            area.auto_preset_away = str(data["away_preset"])

        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting auto preset for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_heating_type(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set heating type configuration for area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: {"heating_type": "radiator"|"floor_heating", "custom_overhead_temp": float (optional)}

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        # Validate and set heating type
        if "heating_type" in data:
            heating_type = data["heating_type"]
            if heating_type not in ["radiator", "floor_heating"]:
                return web.json_response(
                    {"error": "heating_type must be 'radiator' or 'floor_heating'"},
                    status=400,
                )
            area.heating_type = heating_type
            _LOGGER.info("Area %s: Setting heating_type to %s", area_id, heating_type)

        # Set custom overhead temperature (optional)
        if "custom_overhead_temp" in data:
            custom_overhead = data["custom_overhead_temp"]
            if custom_overhead is not None:
                # Validate range
                if custom_overhead < 0 or custom_overhead > 30:
                    return web.json_response(
                        {"error": "custom_overhead_temp must be between 0 and 30°C"},
                        status=400,
                    )
                area.custom_overhead_temp = float(custom_overhead)
                _LOGGER.info(
                    "Area %s: Setting custom_overhead_temp to %.1f°C",
                    area_id,
                    custom_overhead,
                )
            else:
                area.custom_overhead_temp = None
                _LOGGER.info("Area %s: Clearing custom_overhead_temp", area_id)

        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting heating type for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_area_heating_curve(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set per-area heating curve coefficient and whether to use global default.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager
        area_id: Area identifier
        data: Dict containing `use_global` (bool) and/or `coefficient` (float)

    Returns:
        web.Response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            return web.json_response({"error": f"Area {area_id} not found"}, status=404)

        if "use_global" in data:
            use_global = bool(data["use_global"])
            if use_global:
                area.heating_curve_coefficient = None
            else:
                # If toggling off and we have an existing coefficient, keep it
                if area.heating_curve_coefficient is None:
                    area.heating_curve_coefficient = float(
                        area_manager.default_heating_curve_coefficient
                    )

        if "coefficient" in data:
            try:
                coeff = float(data["coefficient"])
            except Exception:
                return web.json_response({"error": "Invalid coefficient"}, status=400)
            if coeff <= 0 or coeff > 10:
                return web.json_response(
                    {"error": "Coefficient must be > 0 and <= 10"}, status=400
                )
            area.heating_curve_coefficient = coeff

        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            from ..utils.coordinator_helpers import call_maybe_async

            await call_maybe_async(coordinator.async_request_refresh)

        return web.json_response({"success": True})
    except Exception as err:
        _LOGGER.error("Error setting area heating curve for %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_set_area_preset_config(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set per-area preset configuration (use global vs custom temperatures).

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Dictionary with use_global_* flags

    Returns:
        JSON response
    """
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    changes = {
        k: v
        for k, v in data.items()
        if k.startswith("use_global_") or k.endswith("_temp")
    }
    _LOGGER.warning("⚙️  API: SET PRESET CONFIG for %s: %s", area.name, changes)

    # Update use_global_* flags
    if "use_global_away" in data:
        area.use_global_away = bool(data["use_global_away"])
    if "use_global_eco" in data:
        area.use_global_eco = bool(data["use_global_eco"])
    if "use_global_comfort" in data:
        area.use_global_comfort = bool(data["use_global_comfort"])
    if "use_global_home" in data:
        area.use_global_home = bool(data["use_global_home"])
    if "use_global_sleep" in data:
        area.use_global_sleep = bool(data["use_global_sleep"])
    if "use_global_activity" in data:
        area.use_global_activity = bool(data["use_global_activity"])
    if "use_global_presence" in data:
        area.use_global_presence = bool(data["use_global_presence"])

    # Update custom temperature values
    if "away_temp" in data:
        area.away_temp = float(data["away_temp"])
    if "eco_temp" in data:
        area.eco_temp = float(data["eco_temp"])
    if "comfort_temp" in data:
        area.comfort_temp = float(data["comfort_temp"])
    if "home_temp" in data:
        area.home_temp = float(data["home_temp"])
    if "sleep_temp" in data:
        area.sleep_temp = float(data["sleep_temp"])
    if "activity_temp" in data:
        area.activity_temp = float(data["activity_temp"])

    # Save to storage
    await area_manager.async_save()

    _LOGGER.warning("✓ Preset config saved for %s", area.name)

    # Refresh coordinator to update frontend
    coordinator = get_coordinator(hass)
    if coordinator:
        from ..utils.coordinator_helpers import call_maybe_async

        await call_maybe_async(coordinator.async_request_refresh)

    return web.json_response({"success": True})


async def handle_set_manual_override(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Toggle manual override mode for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Dictionary with 'enabled' boolean

    Returns:
        JSON response
    """
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    enabled = data.get("enabled")
    if enabled is None:
        return web.json_response({"error": "enabled field is required"}, status=400)

    old_state = area.manual_override
    area.manual_override = bool(enabled)

    _LOGGER.warning(
        "🎛️ API: MANUAL OVERRIDE for %s: %s → %s",
        area.name,
        "ON" if old_state else "OFF",
        "ON" if area.manual_override else "OFF",
    )

    # If turning off manual override and there's an active preset, update target to preset temp
    if not area.manual_override and area.preset_mode and area.preset_mode != "none":
        effective_temp = area.get_effective_target_temperature()
        old_target = area.target_temperature
        # Update the base target temperature to match the preset temperature
        # This ensures the UI shows the correct temperature
        area.target_temperature = effective_temp
        _LOGGER.warning(
            "✓ %s now using preset mode '%s': %.1f°C → %.1f°C",
            area.name,
            area.preset_mode,
            old_target,
            effective_temp,
        )

    # Save to storage
    await area_manager.async_save()

    # Trigger climate control to apply changes
    climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
    if climate_controller:
        await climate_controller.async_control_heating()

    # Refresh coordinator
    coordinator = get_coordinator(hass)
    if coordinator:
        from ..utils.coordinator_helpers import call_maybe_async

        await call_maybe_async(coordinator.async_request_refresh)

    return web.json_response({"success": True})


async def handle_set_primary_temperature_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set the primary temperature sensor for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Dictionary with 'sensor_id' (can be None to reset)

    Returns:
        JSON response
    """
    area = area_manager.get_area(area_id)
    if not area:
        return web.json_response({"error": f"Area {area_id} not found"}, status=404)

    sensor_id = data.get("sensor_id")

    # Validate sensor exists in area if not None
    if sensor_id is not None:
        all_temp_devices = area.get_temperature_sensors() + area.get_thermostats()
        if sensor_id not in all_temp_devices:
            return web.json_response(
                {"error": f"Device {sensor_id} not found in area {area_id}"}, status=400
            )

    old_sensor = area.primary_temperature_sensor
    area.primary_temperature_sensor = sensor_id

    _LOGGER.warning(
        "🌡️ API: PRIMARY TEMP SENSOR for %s: %s → %s",
        area.name,
        old_sensor or "Auto (all sensors)",
        sensor_id or "Auto (all sensors)",
    )

    # Save to storage
    await area_manager.async_save()

    # Update temperatures immediately
    climate_controller = hass.data.get(DOMAIN, {}).get("climate_controller")
    if climate_controller:
        await climate_controller.async_update_area_temperatures()
        await climate_controller.async_control_heating()

    # Refresh coordinator
    coordinator = get_coordinator(hass)
    if coordinator:
        from ..utils.coordinator_helpers import call_maybe_async

        await call_maybe_async(coordinator.async_request_refresh)

    return web.json_response({"success": True})
