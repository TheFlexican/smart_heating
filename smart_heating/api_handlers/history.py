"""History and learning API handlers for Smart Heating."""

import logging
from datetime import datetime
from aiohttp import web
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, HISTORY_RECORD_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

ERROR_HISTORY_NOT_AVAILABLE = "History not available"


async def handle_get_history(hass: HomeAssistant, area_id: str, request) -> web.Response:
    """Get temperature history for an area.
    
    Args:
        hass: Home Assistant instance
        area_id: Area identifier
        request: Request object for query parameters
        
    Returns:
        JSON response with history
    """
    # Get query parameters
    hours = request.query.get("hours")
    start_time = request.query.get("start_time")
    end_time = request.query.get("end_time")
    
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response(
            {"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503
        )
    
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        hours_int = None
        
        if start_time and end_time:
            # Custom time range
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            history = history_tracker.get_history(area_id, start_time=start_dt, end_time=end_dt)
        elif hours:
            # Hours-based query
            hours_int = int(hours)
            history = history_tracker.get_history(area_id, hours=hours_int)
        else:
            # Default: last 24 hours
            hours_int = 24
            history = history_tracker.get_history(area_id, hours=hours_int)
        
        return web.json_response({
            "area_id": area_id,
            "hours": hours_int,
            "start_time": start_time,
            "end_time": end_time,
            "entries": history,
            "count": len(history)
        })
    except ValueError as err:
        return web.json_response(
            {"error": f"Invalid time parameter: {err}"}, status=400
        )


async def handle_get_learning_stats(hass: HomeAssistant, area_id: str) -> web.Response:
    """Get learning statistics for an area.
    
    Args:
        hass: Home Assistant instance
        area_id: Area identifier
        
    Returns:
        JSON response with learning stats
    """
    learning_engine = hass.data.get(DOMAIN, {}).get("learning_engine")
    if not learning_engine:
        return web.json_response(
            {"error": "Learning engine not available"}, status=503
        )
    
    stats = await learning_engine.async_get_learning_stats(area_id)
    
    return web.json_response({
        "area_id": area_id,
        "stats": stats
    })


async def handle_get_history_config(hass: HomeAssistant) -> web.Response:
    """Get history configuration.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        JSON response with history settings
    """
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response(
            {"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503
        )
    
    return web.json_response({
        "retention_days": history_tracker.get_retention_days(),
        "record_interval_seconds": HISTORY_RECORD_INTERVAL_SECONDS,
        "record_interval_minutes": HISTORY_RECORD_INTERVAL_SECONDS / 60
    })


async def handle_set_history_config(hass: HomeAssistant, data: dict) -> web.Response:
    """Set history configuration.
    
    Args:
        hass: Home Assistant instance
        data: Configuration data
        
    Returns:
        JSON response
    """
    retention_days = data.get("retention_days")
    if not retention_days:
        return web.json_response(
            {"error": "retention_days required"}, status=400
        )
    
    try:
        history_tracker = hass.data.get(DOMAIN, {}).get("history")
        if not history_tracker:
            return web.json_response(
                {"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503
            )
        
        history_tracker.set_retention_days(int(retention_days))
        await history_tracker.async_save()
        
        # Trigger cleanup if retention was reduced
        await history_tracker._async_cleanup_old_entries()
        
        return web.json_response({
            "success": True,
            "retention_days": history_tracker.get_retention_days()
        })
    except ValueError as err:
        return web.json_response(
            {"error": str(err)}, status=400
        )
