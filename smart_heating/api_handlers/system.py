"""System API handlers for Smart Heating."""

import logging
from aiohttp import web
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def handle_get_status(area_manager: AreaManager) -> web.Response:
    """Get system status.
    
    Args:
        area_manager: Area manager instance
        
    Returns:
        JSON response with status
    """
    areas = area_manager.get_all_areas()
    
    status = {
        "area_count": len(areas),
        "active_areas": sum(1 for z in areas.values() if z.enabled),
        "total_devices": sum(len(z.devices) for z in areas.values()),
    }
    
    return web.json_response(status)


async def handle_get_entity_state(hass: HomeAssistant, entity_id: str) -> web.Response:
    """Get entity state from Home Assistant.
    
    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to fetch
        
    Returns:
        JSON response with entity state
    """
    state = hass.states.get(entity_id)
    
    if not state:
        return web.json_response(
            {"error": f"Entity {entity_id} not found"}, status=404
        )
    
    return web.json_response({
        "state": state.state,
        "attributes": dict(state.attributes),
        "last_changed": state.last_changed.isoformat(),
        "last_updated": state.last_updated.isoformat(),
    })


async def handle_call_service(hass: HomeAssistant, data: dict) -> web.Response:
    """Call a Home Assistant service.
    
    Args:
        hass: Home Assistant instance
        data: Service call data
        
    Returns:
        JSON response
    """
    service_name = data.get("service")
    if not service_name:
        return web.json_response(
            {"error": "Service name required"}, status=400
        )
    
    try:
        service_data = {k: v for k, v in data.items() if k != "service"}
        
        await hass.services.async_call(
            "smart_heating",
            service_name,
            service_data,
            blocking=True,
        )
        
        return web.json_response({
            "success": True,
            "message": f"Service {service_name} called successfully"
        })
    except Exception as err:
        _LOGGER.error("Error calling service %s: %s", service_name, err)
        return web.json_response(
            {"error": str(err)}, status=500
        )
