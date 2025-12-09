"""Configuration API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..const import DOMAIN
from ..utils import get_coordinator

_LOGGER = logging.getLogger(__name__)


async def handle_get_config(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Get system configuration.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with configuration
    """
    config = {
        "opentherm_gateway_id": area_manager.opentherm_gateway_id,
        "opentherm_enabled": area_manager.opentherm_enabled,
        "trv_heating_temp": area_manager.trv_heating_temp,
        "trv_idle_temp": area_manager.trv_idle_temp,
        "trv_temp_offset": area_manager.trv_temp_offset,
        "safety_sensors": area_manager.get_safety_sensors(),
        "safety_alert_active": area_manager.is_safety_alert_active(),
        "hide_devices_panel": area_manager.hide_devices_panel,
    }

    return web.json_response(config)


async def handle_get_global_presets(area_manager: AreaManager) -> web.Response:
    """Get global preset temperatures.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with global preset temperatures
    """
    return web.json_response(
        {
            "away_temp": area_manager.global_away_temp,
            "eco_temp": area_manager.global_eco_temp,
            "comfort_temp": area_manager.global_comfort_temp,
            "home_temp": area_manager.global_home_temp,
            "sleep_temp": area_manager.global_sleep_temp,
            "activity_temp": area_manager.global_activity_temp,
        }
    )


async def handle_set_global_presets(
    area_manager: AreaManager, data: dict
) -> web.Response:
    """Set global preset temperatures.

    Args:
        area_manager: Area manager instance
        data: Dictionary with preset temperatures to update

    Returns:
        JSON response
    """
    # Log what's changing
    changes = {k: v for k, v in data.items() if k.endswith("_temp")}
    _LOGGER.warning("🌍 API: SET GLOBAL PRESETS: %s", changes)

    # Update global preset temperatures
    if "away_temp" in data:
        old = area_manager.global_away_temp
        area_manager.global_away_temp = float(data["away_temp"])
        _LOGGER.warning(
            "  Global Away: %.1f°C → %.1f°C", old, area_manager.global_away_temp
        )
    if "eco_temp" in data:
        old = area_manager.global_eco_temp
        area_manager.global_eco_temp = float(data["eco_temp"])
        _LOGGER.warning(
            "  Global Eco: %.1f°C → %.1f°C", old, area_manager.global_eco_temp
        )
    if "comfort_temp" in data:
        old = area_manager.global_comfort_temp
        area_manager.global_comfort_temp = float(data["comfort_temp"])
        _LOGGER.warning(
            "  Global Comfort: %.1f°C → %.1f°C", old, area_manager.global_comfort_temp
        )
    if "home_temp" in data:
        old = area_manager.global_home_temp
        area_manager.global_home_temp = float(data["home_temp"])
        _LOGGER.warning(
            "  Global Home: %.1f°C → %.1f°C", old, area_manager.global_home_temp
        )
    if "sleep_temp" in data:
        old = area_manager.global_sleep_temp
        area_manager.global_sleep_temp = float(data["sleep_temp"])
        _LOGGER.warning(
            "  Global Sleep: %.1f°C → %.1f°C", old, area_manager.global_sleep_temp
        )
    if "activity_temp" in data:
        old = area_manager.global_activity_temp
        area_manager.global_activity_temp = float(data["activity_temp"])
        _LOGGER.warning(
            "  Global Activity: %.1f°C → %.1f°C", old, area_manager.global_activity_temp
        )

    # Save to storage
    await area_manager.async_save()

    _LOGGER.warning("✓ Global presence saved")

    return web.json_response({"success": True})


async def handle_get_hysteresis(area_manager: AreaManager) -> web.Response:
    """Get global hysteresis value.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with hysteresis value
    """
    return web.json_response({"hysteresis": area_manager.hysteresis})


async def handle_set_opentherm_gateway(
    area_manager: AreaManager, coordinator, data: dict
) -> web.Response:
    """Set OpenTherm Gateway configuration.

    Args:
        area_manager: Area manager instance
        coordinator: Coordinator instance (for refresh)
        data: Dictionary with gateway_id and enabled

    Returns:
        JSON response
    """
    gateway_id = data.get("gateway_id")
    enabled = data.get("enabled", True)

    await area_manager.set_opentherm_gateway(gateway_id, enabled)

    # Refresh coordinator to update state
    if coordinator:
        await coordinator.async_request_refresh()

    _LOGGER.info(
        "OpenTherm Gateway configured: gateway_id=%s, enabled=%s", gateway_id, enabled
    )

    return web.json_response({"success": True})


async def handle_set_hide_devices_panel(
    area_manager: AreaManager, data: dict
) -> web.Response:
    """Set hide devices panel setting.

    Args:
        area_manager: Area manager instance
        data: Dictionary with hide_devices_panel boolean

    Returns:
        JSON response
    """
    if "hide_devices_panel" in data:
        area_manager.hide_devices_panel = bool(data["hide_devices_panel"])
        await area_manager.async_save()
        _LOGGER.info("✓ Hide devices panel set to: %s", area_manager.hide_devices_panel)
        return web.json_response({"success": True})

    return web.json_response({"error": "Missing hide_devices_panel value"}, status=400)


async def handle_get_opentherm_config(area_manager: AreaManager) -> web.Response:
    """Get global hysteresis value.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with hysteresis value
    """
    return web.json_response({"hysteresis": area_manager.hysteresis})


async def handle_set_hysteresis_value(
    hass: HomeAssistant, area_manager: AreaManager, coordinator, data: dict
) -> web.Response:
    """Set global hysteresis value.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        coordinator: Coordinator instance
        data: Dictionary with hysteresis value

    Returns:
        JSON response
    """
    _LOGGER.info("🌡️ API: SET HYSTERESIS: %s", data)

    if "hysteresis" in data:
        hysteresis = float(data["hysteresis"])
        # Validate range
        if hysteresis < 0.1 or hysteresis > 2.0:
            return web.json_response(
                {"error": "Hysteresis must be between 0.1 and 2.0°C"}, status=400
            )

        # Update area manager
        area_manager.hysteresis = hysteresis
        await area_manager.async_save()

        # Update all climate controllers
        for area in area_manager.areas.values():
            if hasattr(area, "climate_controller") and area.climate_controller:
                area.climate_controller._hysteresis = hysteresis

        # Request coordinator update
        if coordinator:
            await coordinator.async_request_refresh()

        _LOGGER.info("✅ Hysteresis updated to %.1f°C", hysteresis)
        return web.json_response({"success": True})

    return web.json_response({"error": "Missing hysteresis value"}, status=400)


async def handle_get_global_presence(area_manager: AreaManager) -> web.Response:
    """Get global presence sensors.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with global presence sensors
    """
    return web.json_response({"sensors": area_manager.global_presence_sensors})


async def handle_set_global_presence(
    area_manager: AreaManager, data: dict
) -> web.Response:
    """Set global presence sensors.

    Args:
        area_manager: Area manager instance
        data: Dictionary with sensors list

    Returns:
        JSON response
    """
    _LOGGER.warning("🌍 API: SET GLOBAL PRESENCE: %s", data)

    if "sensors" in data:
        area_manager.global_presence_sensors = data["sensors"]
        _LOGGER.warning(
            "  Global presence sensors updated: %d sensors",
            len(area_manager.global_presence_sensors),
        )

    # Save to storage
    await area_manager.async_save()

    _LOGGER.warning("✓ Global presence saved")

    return web.json_response({"success": True})


async def handle_set_frost_protection(
    area_manager: AreaManager, data: dict
) -> web.Response:
    """Set global frost protection settings.

    Args:
        area_manager: Area manager instance
        data: Request data with enabled and temperature

    Returns:
        JSON response
    """
    enabled = data.get("enabled")
    temp = data.get("temperature")

    try:
        if enabled is not None:
            area_manager.frost_protection_enabled = enabled
        if temp is not None:
            area_manager.frost_protection_temp = temp

        await area_manager.async_save()

        return web.json_response(
            {
                "success": True,
                "enabled": area_manager.frost_protection_enabled,
                "temperature": area_manager.frost_protection_temp,
            }
        )
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_get_vacation_mode(hass: HomeAssistant) -> web.Response:
    """Get vacation mode status and configuration.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with vacation mode data
    """
    vacation_manager = hass.data[DOMAIN].get("vacation_manager")
    if not vacation_manager:
        return web.json_response(
            {"error": "Vacation manager not initialized"}, status=500
        )

    return web.json_response(vacation_manager.get_data())


async def handle_enable_vacation_mode(hass: HomeAssistant, data: dict) -> web.Response:
    """Enable vacation mode.

    Args:
        hass: Home Assistant instance
        data: Dictionary with vacation mode configuration

    Returns:
        JSON response with updated vacation mode data
    """
    vacation_manager = hass.data[DOMAIN].get("vacation_manager")
    if not vacation_manager:
        return web.json_response(
            {"error": "Vacation manager not initialized"}, status=500
        )

    start_date = data.get("start_date")
    end_date = data.get("end_date")
    temperature = data.get("temperature")

    if not start_date or not end_date:
        return web.json_response(
            {"error": "start_date and end_date are required"}, status=400
        )

    try:
        await vacation_manager.async_enable(
            start_date=start_date, end_date=end_date, temperature=temperature
        )

        return web.json_response(vacation_manager.get_data())
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_disable_vacation_mode(hass: HomeAssistant) -> web.Response:
    """Disable vacation mode.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response
    """
    vacation_manager = hass.data[DOMAIN].get("vacation_manager")
    if not vacation_manager:
        return web.json_response(
            {"error": "Vacation manager not initialized"}, status=500
        )

    await vacation_manager.async_disable()

    return web.json_response({"success": True})


async def handle_get_safety_sensor(area_manager: AreaManager) -> web.Response:
    """Get safety sensor configuration.

    Args:
        area_manager: Area manager instance

    Returns:
        JSON response with safety sensor data
    """
    sensors = area_manager.get_safety_sensors()

    # Return first sensor if exists, otherwise empty config
    if sensors:
        return web.json_response(
            {
                "sensor_id": sensors[0].get("sensor_id"),
                "enabled": sensors[0].get("enabled", True),
                "alert_active": area_manager.is_safety_alert_active(),
            }
        )
    else:
        return web.json_response(
            {"sensor_id": None, "enabled": False, "alert_active": False}
        )


async def handle_set_safety_sensor(
    hass: HomeAssistant, area_manager: AreaManager, data: dict
) -> web.Response:
    """Set safety sensor (replaces existing).

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        data: Dictionary with sensor_id

    Returns:
        JSON response
    """
    sensor_id = data.get("sensor_id")
    if not sensor_id:
        return web.json_response({"error": "sensor_id is required"}, status=400)

    # Clear existing sensors and add new one
    area_manager.clear_safety_sensors()
    area_manager.add_safety_sensor(sensor_id)
    await area_manager.async_save()

    # Reconfigure safety monitor
    safety_monitor = hass.data[DOMAIN].get("safety_monitor")
    if safety_monitor:
        await safety_monitor.async_reconfigure()

    # Broadcast configuration change via WebSocket
    hass.bus.async_fire(
        f"{DOMAIN}_safety_sensor_changed", {"sensor_id": sensor_id, "enabled": True}
    )

    _LOGGER.info("Safety sensor set to %s via API", sensor_id)
    return web.json_response({"success": True, "sensor_id": sensor_id})


async def handle_remove_safety_sensor(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Remove safety sensor.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response
    """
    area_manager.clear_safety_sensors()
    await area_manager.async_save()

    # Reconfigure safety monitor
    safety_monitor = hass.data[DOMAIN].get("safety_monitor")
    if safety_monitor:
        await safety_monitor.async_reconfigure()

    # Broadcast configuration change via WebSocket
    hass.bus.async_fire(
        f"{DOMAIN}_safety_sensor_changed", {"sensor_id": None, "enabled": False}
    )

    _LOGGER.info("Safety sensor removed via API")
    return web.json_response({"success": True})


async def handle_set_hvac_mode(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Set HVAC mode for an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with hvac_mode

    Returns:
        JSON response
    """
    hvac_mode = data.get("hvac_mode")
    if not hvac_mode:
        return web.json_response({"error": "hvac_mode required"}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.hvac_mode = hvac_mode
        await area_manager.async_save()

        # Refresh coordinator
        coordinator = get_coordinator(hass)
        if coordinator:
            await coordinator.async_request_refresh()

        return web.json_response({"success": True, "hvac_mode": hvac_mode})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)
