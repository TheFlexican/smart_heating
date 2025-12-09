"""Sensor API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def handle_add_window_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add window sensor to an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with configuration

    Returns:
        JSON response
    """
    entity_id = data.get("entity_id")
    if not entity_id:
        return web.json_response({"error": "entity_id required"}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        # Extract configuration parameters
        action_when_open = data.get("action_when_open", "reduce_temperature")
        temp_drop = data.get("temp_drop")

        area.add_window_sensor(entity_id, action_when_open, temp_drop)
        await area_manager.async_save()

        # Refresh coordinator
        entry_ids = [
            key
            for key in hass.data[DOMAIN].keys()
            if key
            not in [
                "history",
                "climate_controller",
                "schedule_executor",
                "climate_unsub",
                "learning_engine",
                "area_logger",
                "vacation_manager",
                "safety_monitor",
            ]
        ]
        if entry_ids:
            coordinator = hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()

        return web.json_response({"success": True, "entity_id": entity_id})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_remove_window_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, entity_id: str
) -> web.Response:
    """Remove window sensor from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        entity_id: Entity ID to remove

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.remove_window_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        entry_ids = [
            key
            for key in hass.data[DOMAIN].keys()
            if key
            not in [
                "history",
                "climate_controller",
                "schedule_executor",
                "climate_unsub",
                "learning_engine",
                "area_logger",
                "vacation_manager",
                "safety_monitor",
            ]
        ]
        if entry_ids:
            coordinator = hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


async def handle_add_presence_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, data: dict
) -> web.Response:
    """Add presence sensor to an area.

    Presence sensors control preset mode switching:
    - When away: Switch to "away" preset
    - When home: Switch back to previous preset

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        data: Request data with entity_id

    Returns:
        JSON response
    """
    entity_id = data.get("entity_id")
    if not entity_id:
        return web.json_response({"error": "entity_id required"}, status=400)

    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.add_presence_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        entry_ids = [
            key
            for key in hass.data[DOMAIN].keys()
            if key
            not in [
                "history",
                "climate_controller",
                "schedule_executor",
                "climate_unsub",
                "learning_engine",
                "area_logger",
                "vacation_manager",
                "safety_monitor",
            ]
        ]
        if entry_ids:
            coordinator = hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()

        return web.json_response({"success": True, "entity_id": entity_id})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_remove_presence_sensor(
    hass: HomeAssistant, area_manager: AreaManager, area_id: str, entity_id: str
) -> web.Response:
    """Remove presence sensor from an area.

    Args:
        hass: Home Assistant instance
        area_manager: Area manager instance
        area_id: Area identifier
        entity_id: Entity ID to remove

    Returns:
        JSON response
    """
    try:
        area = area_manager.get_area(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        area.remove_presence_sensor(entity_id)
        await area_manager.async_save()

        # Refresh coordinator
        entry_ids = [
            key
            for key in hass.data[DOMAIN].keys()
            if key
            not in [
                "history",
                "climate_controller",
                "schedule_executor",
                "climate_unsub",
                "learning_engine",
                "area_logger",
                "vacation_manager",
                "safety_monitor",
            ]
        ]
        if entry_ids:
            coordinator = hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()

        return web.json_response({"success": True})
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=404)


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_binary_sensor_entities(hass: HomeAssistant) -> web.Response:
    """Get all binary sensor entities from Home Assistant.

    Also includes person and device_tracker entities for presence detection.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of binary sensor entities
    """
    entities = []

    # Get binary sensors
    for entity_id in hass.states.async_entity_ids("binary_sensor"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": state.attributes.get("device_class"),
                    },
                }
            )

    # Get person entities (for presence detection)
    for entity_id in hass.states.async_entity_ids("person"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    },
                }
            )

    # Get device_tracker entities (for presence detection)
    for entity_id in hass.states.async_entity_ids("device_tracker"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    },
                }
            )

    return web.json_response({"entities": entities})


# noqa: ASYNC109 - Web API handlers must be async per aiohttp convention
async def handle_get_weather_entities(hass: HomeAssistant) -> web.Response:
    """Get all weather entities from Home Assistant.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with list of weather entities
    """
    entities = []

    # Get weather entities
    for entity_id in hass.states.async_entity_ids("weather"):
        state = hass.states.get(entity_id)
        if state:
            entities.append(
                {
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                    },
                }
            )

    return web.json_response({"entities": entities})
