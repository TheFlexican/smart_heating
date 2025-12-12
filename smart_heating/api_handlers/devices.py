"""Device API handlers for Smart Heating."""

import asyncio
import logging
import time

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from ..area_manager import AreaManager
from ..models import Area

_LOGGER = logging.getLogger(__name__)

# Device discovery cache
_devices_cache = None
_cache_timestamp = None


async def handle_get_devices(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Get available devices from Home Assistant.

    Returns cached device list if available. Use /devices/refresh for fresh discovery.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with available devices
    """
    # Return cached devices if available
    if _devices_cache is not None:
        _LOGGER.debug("Returning cached device list (%d devices)", len(_devices_cache))
        return web.json_response({"devices": _devices_cache})

    # No cache, perform discovery
    _LOGGER.info("No device cache available, performing initial discovery")
    return await _discover_devices(hass, area_manager)


async def _discover_devices(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Discover climate, switch, and temperature sensor devices from Home Assistant.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with discovered devices
    """
    await asyncio.sleep(0)  # Minimal async operation to satisfy async requirement
    global _devices_cache, _cache_timestamp

    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)
    area_registry = ar.async_get(hass)

    # Get all climate, switch, and temperature sensor entities
    all_entities = _get_discoverable_entities(entity_reg, hass)

    devices = []

    for entry in all_entities:
        devices.append(
            _build_device_payload(entry, device_reg, area_registry, hass, area_manager)
        )

    # Cache the results
    _devices_cache = devices
    _cache_timestamp = time.time()

    # Count by type
    thermostat_count = sum(1 for d in devices if d["type"] == "climate")
    switch_count = sum(1 for d in devices if d["type"] == "switch")
    temp_sensor_count = sum(1 for d in devices if d["type"] == "temperature_sensor")

    _LOGGER.info(
        "Discovered %d devices (%d thermostats, %d switches, %d temperature sensors)",
        len(devices),
        thermostat_count,
        switch_count,
        temp_sensor_count,
    )

    return web.json_response({"devices": devices})


def _get_discoverable_entities(entity_reg, hass):
    """Return a list of entities that we should consider for discovery.

    This includes climate and switch entities and sensors with the temperature device class.
    """
    result = []
    for entry in entity_reg.entities.values():
        if entry.domain in ("climate", "switch"):
            result.append(entry)
        elif entry.domain == "sensor":
            state = hass.states.get(entry.entity_id)
            if state and state.attributes.get("device_class") == "temperature":
                result.append(entry)
    return result


def _build_device_payload(entry, device_reg, area_registry, hass, area_manager):
    """Build a device payload dict for a given registry entry.

    Returns a dictionary suitable for API responses.
    """
    device_type = _determine_device_type(entry)

    device_name, device_area_id, device_area_name = _get_device_name_and_area(
        entry, device_reg, area_registry
    )

    if not device_name:
        device_name = entry.original_name or entry.entity_id

    current_state, current_temp = _get_current_state_and_temperature(entry, hass)

    assigned_to_area = _find_assigned_to_area(entry.entity_id, area_manager)

    return {
        "id": entry.entity_id,
        "name": device_name,
        "type": device_type,
        "state": current_state,
        "current_temperature": current_temp,
        "area_id": device_area_id,
        "area_name": device_area_name,
        "assigned_to_area": assigned_to_area,
    }


def _determine_device_type(entry):
    if entry.domain == "climate":
        return "climate"
    if entry.domain == "switch":
        return "switch"
    return "temperature_sensor"


def _get_device_name_and_area(entry, device_reg, area_registry):
    device_name = None
    device_area_id = None
    device_area_name = None

    if entry.device_id:
        device = device_reg.async_get(entry.device_id)
        if device:
            device_name = device.name_by_user or device.name
            if device.area_id:
                device_area_id = device.area_id
                area = area_registry.async_get_area(device.area_id)
                if area:
                    device_area_name = area.name

    if not device_name:
        device_name = entry.original_name or entry.entity_id

    return device_name, device_area_id, device_area_name


def _get_current_state_and_temperature(entry, hass):
    state = hass.states.get(entry.entity_id)
    current_state = state.state if state else "unavailable"
    current_temp = None
    if entry.domain == "climate" and state:
        current_temp = state.attributes.get("current_temperature")
    return current_state, current_temp


def _find_assigned_to_area(entity_id, area_manager: AreaManager):
    for area_id, area in area_manager.get_all_areas().items():
        if entity_id in area.devices:
            return area_id
    return None


async def handle_refresh_devices(
    hass: HomeAssistant, area_manager: AreaManager
) -> web.Response:
    """Refresh device list and update any assigned devices.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance

    Returns:
        JSON response with refresh results
    """
    global _devices_cache, _cache_timestamp

    try:
        _LOGGER.info("Refreshing device discovery...")

        # Clear cache and rediscover
        _devices_cache = None
        _cache_timestamp = None
        response = await _discover_devices(hass, area_manager)

        # Parse the response to get device list
        import json

        devices_data = json.loads(response.text)
        devices = devices_data.get("devices", [])

        # Update assigned devices with latest info
        updated_count = 0
        added_count = len(devices)

        for area in area_manager.get_all_areas().values():
            for device_id in area.devices.keys():
                # Find device in discovered list
                device_info = next((d for d in devices if d["id"] == device_id), None)
                if device_info:
                    # Update device type if changed
                    if area.devices[device_id].get("type") != device_info["type"]:
                        area.devices[device_id]["type"] = device_info["type"]
                        updated_count += 1
                else:
                    _LOGGER.warning(
                        "Device %s assigned to area %s no longer exists",
                        device_id,
                        area.name,
                    )

        # Save if anything changed
        if updated_count > 0:
            await area_manager.async_save()

        return web.json_response(
            {
                "success": True,
                "updated": updated_count,
                "available": added_count,
                "cached_devices": len(_devices_cache) if _devices_cache else 0,
                "message": f"Refreshed {updated_count} devices, {added_count} available for assignment",
            }
        )

    except Exception as err:
        _LOGGER.error("Error refreshing devices: %s", err)
        return web.json_response({"error": str(err)}, status=500)


async def handle_add_device(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add a device to a area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Device data

    Returns:
        JSON response
    """
    device_id = data.get("device_id")
    device_type = data.get("device_type")
    mqtt_topic = data.get("mqtt_topic")

    if not device_id or not device_type:
        return web.json_response(
            {"error": "device_id and device_type are required"}, status=400
        )

    try:
        # Ensure area exists in storage
        if area_manager.get_area(area_id) is None:
            # Auto-create area entry for this HA area if not exists
            area_registry = ar.async_get(hass)
            ha_area = area_registry.async_get_area(area_id)
            if ha_area:
                # Create internal storage for this HA area
                area = Area(area_id, ha_area.name)
                area.area_manager = area_manager
                area_manager.areas[area_id] = area
            else:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )

        area_manager.add_device_to_area(area_id, device_id, device_type, mqtt_topic)
        await area_manager.async_save()

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_remove_device(
    area_manager: AreaManager, area_id: str, device_id: str
) -> web.Response:
    """Remove a device from a area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        device_id: Device identifier

    Returns:
        JSON response
    """
    try:
        area_manager.remove_device_from_area(area_id, device_id)
        await area_manager.async_save()

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)
