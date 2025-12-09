"""History and learning API handlers for Smart Heating."""

import logging
from datetime import datetime

from aiohttp import web
from homeassistant.core import HomeAssistant

from ..const import DOMAIN, HISTORY_RECORD_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

ERROR_HISTORY_NOT_AVAILABLE = "History not available"


async def handle_get_history(
    hass: HomeAssistant, area_id: str, request
) -> web.Response:
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
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        hours_int = None

        if start_time and end_time:
            # Custom time range
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            history = history_tracker.get_history(
                area_id, start_time=start_dt, end_time=end_dt
            )
        elif hours:
            # Hours-based query
            hours_int = int(hours)
            history = history_tracker.get_history(area_id, hours=hours_int)
        else:
            # Default: last 24 hours
            hours_int = 24
            history = history_tracker.get_history(area_id, hours=hours_int)

        return web.json_response(
            {
                "area_id": area_id,
                "hours": hours_int,
                "start_time": start_time,
                "end_time": end_time,
                "entries": history,
                "count": len(history),
            }
        )
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
        return web.json_response({"error": "Learning engine not available"}, status=503)

    stats = await learning_engine.async_get_learning_stats(area_id)

    return web.json_response({"area_id": area_id, "stats": stats})


async def handle_get_history_config(hass: HomeAssistant) -> web.Response:
    """Get history configuration.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with history settings
    """
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    return web.json_response(
        {
            "retention_days": history_tracker.get_retention_days(),
            "storage_backend": history_tracker.get_storage_backend(),
            "record_interval_seconds": HISTORY_RECORD_INTERVAL_SECONDS,
            "record_interval_minutes": HISTORY_RECORD_INTERVAL_SECONDS / 60,
        }
    )


async def handle_set_history_config(hass: HomeAssistant, data: dict) -> web.Response:
    """Set history configuration.

    Args:
        hass: Home Assistant instance
        data: Configuration data (retention_days required, storage_backend optional)

    Returns:
        JSON response
    """
    retention_days = data.get("retention_days")
    if not retention_days:
        return web.json_response({"error": "retention_days required"}, status=400)

    try:
        history_tracker = hass.data.get(DOMAIN, {}).get("history")
        if not history_tracker:
            return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

        history_tracker.set_retention_days(int(retention_days))
        
        # Note: storage_backend changes should use the migration API
        # This is just for initial config or to store preference
        storage_backend = data.get("storage_backend")
        if storage_backend:
            _LOGGER.info(
                "Storage backend preference set to %s. "
                "Use migration API to switch backends with data migration.",
                storage_backend
            )
        
        await history_tracker.async_save()

        # Trigger cleanup if retention was reduced
        await history_tracker._async_cleanup_old_entries()

        return web.json_response(
            {
                "success": True, 
                "retention_days": history_tracker.get_retention_days(),
                "storage_backend": history_tracker.get_storage_backend()
            }
        )
    except ValueError as err:
        return web.json_response({"error": str(err)}, status=400)


async def handle_get_history_storage_info(hass: HomeAssistant) -> web.Response:
    """Get history storage backend information.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with storage info
    """
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    storage_backend = history_tracker.get_storage_backend()
    response = {
        "storage_backend": storage_backend,
        "retention_days": history_tracker.get_retention_days(),
    }

    # Add database stats if using database backend
    if storage_backend == "database":
        stats = await history_tracker.async_get_database_stats()
        response["database_stats"] = stats

    return web.json_response(response)


async def handle_migrate_history_storage(hass: HomeAssistant, data: dict) -> web.Response:
    """Migrate history between storage backends.

    Args:
        hass: Home Assistant instance
        data: Migration data with target_backend

    Returns:
        JSON response with migration result
    """
    target_backend = data.get("target_backend")
    if not target_backend:
        return web.json_response({"error": "target_backend required"}, status=400)

    if target_backend not in ["json", "database"]:
        return web.json_response(
            {"error": "target_backend must be 'json' or 'database'"}, status=400
        )

    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    result = await history_tracker.async_migrate_storage(target_backend)

    status_code = 200 if result["success"] else 400
    return web.json_response(result, status=status_code)


async def handle_get_database_stats(hass: HomeAssistant) -> web.Response:
    """Get database statistics.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with database stats
    """
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    stats = await history_tracker.async_get_database_stats()
    return web.json_response(stats)


async def handle_cleanup_history(hass: HomeAssistant) -> web.Response:
    """Manually trigger history cleanup.

    Args:
        hass: Home Assistant instance

    Returns:
        JSON response with cleanup result
    """
    history_tracker = hass.data.get(DOMAIN, {}).get("history")
    if not history_tracker:
        return web.json_response({"error": ERROR_HISTORY_NOT_AVAILABLE}, status=503)

    await history_tracker._async_cleanup_old_entries()

    return web.json_response(
        {
            "success": True,
            "message": "History cleanup completed",
            "retention_days": history_tracker.get_retention_days(),
            "storage_backend": history_tracker.get_storage_backend(),
        }
    )
