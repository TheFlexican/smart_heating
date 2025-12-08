"""Logging API handlers for Smart Heating."""

import logging

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def handle_get_area_logs(hass: HomeAssistant, area_id: str, request) -> web.Response:
    """Get logs for a specific area.

    Args:
        hass: Home Assistant instance
        area_id: Area identifier
        request: Request object for query parameters

    Returns:
        JSON response with logs
    """
    try:
        # Get optional query parameters
        limit = request.query.get("limit")
        event_type = request.query.get("type")

        # Get area logger from hass data
        area_logger = hass.data[DOMAIN].get("area_logger")
        if not area_logger:
            return web.json_response({"logs": []})

        # Get logs (async)
        logs = await area_logger.async_get_logs(
            area_id=area_id, limit=int(limit) if limit else None, event_type=event_type
        )

        return web.json_response({"logs": logs})

    except Exception as err:
        _LOGGER.error("Error getting logs for area %s: %s", area_id, err)
        return web.json_response({"error": str(err)}, status=500)
