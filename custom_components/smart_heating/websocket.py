"""WebSocket handler for Smart Heating."""
import asyncio
import logging
from typing import Any

from aiohttp import web
import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.websocket_api import (
    ActiveConnection,
    async_register_command,
    websocket_command,
    result_message,
)

from .const import DOMAIN
from .coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)


@websocket_command({
    "type": "smart_heating/subscribe",
})
@callback
def websocket_subscribe_updates(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to area heater manager updates.
    
    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    @callback
    def forward_messages():
        """Forward coordinator updates to websocket."""
        connection.send_message(result_message(msg["id"], {
            "event": "update",
            "data": coordinator.data
        }))

    # Get the coordinator - filter out non-entry keys
    entry_ids = [
        key for key in hass.data[DOMAIN].keys()
        if key not in ["history", "climate_controller", "schedule_executor"]
    ]
    if not entry_ids:
        connection.send_error(msg["id"], "not_loaded", "Smart Heating not loaded")
        return
    
    entry_id = entry_ids[0]
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry_id]
    
    # Subscribe to coordinator updates
    unsub = coordinator.async_add_listener(forward_messages)
    
    @callback
    def unsub_callback():
        """Unsubscribe from updates."""
        unsub()
    
    connection.subscriptions[msg["id"]] = unsub_callback
    connection.send_result(msg["id"])


@websocket_command({
    "type": "smart_heating/get_areas",
})
@callback
def websocket_get_areas(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all areas via websocket.
    
    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    # Get the coordinator - filter out non-entry keys
    entry_ids = [
        key for key in hass.data[DOMAIN].keys()
        if key not in ["history", "climate_controller", "schedule_executor"]
    ]
    if not entry_ids:
        connection.send_error(msg["id"], "not_loaded", "Smart Heating not loaded")
        return
    
    entry_id = entry_ids[0]
    coordinator: SmartHeatingCoordinator = hass.data[DOMAIN][entry_id]
    area_manager = coordinator.area_manager
    
    areas = area_manager.get_all_areas()
    areas_data = []
    
    for area_id, area in areas.items():
        areas_data.append({
            "id": area.area_id,
            "name": area.name,
            "enabled": area.enabled,
            "state": area.state,
            "target_temperature": area.target_temperature,
            "current_temperature": area.current_temperature,
            "devices": [
                {
                    "id": dev_id,
                    "type": dev_data["type"],
                    "mqtt_topic": dev_data.get("mqtt_topic"),
                }
                for dev_id, dev_data in area.devices.items()
            ],
        })
    
    connection.send_result(msg["id"], {"areas": areas_data})


async def setup_websocket(hass: HomeAssistant) -> None:
    """Set up WebSocket API.
    
    Args:
        hass: Home Assistant instance
    """
    async_register_command(hass, websocket_subscribe_updates)
    async_register_command(hass, websocket_get_areas)
    
    _LOGGER.info("Smart Heating WebSocket API registered")
