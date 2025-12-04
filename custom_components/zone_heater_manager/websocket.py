"""WebSocket handler for Zone Heater Manager."""
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
from .coordinator import ZoneHeaterManagerCoordinator

_LOGGER = logging.getLogger(__name__)


@websocket_command({
    "type": "zone_heater_manager/subscribe",
})
@callback
def websocket_subscribe_updates(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to zone heater manager updates.
    
    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    @callback
    def forward_messages(event):
        """Forward coordinator updates to websocket."""
        connection.send_message(result_message(msg["id"], {
            "event": "update",
            "data": event.data
        }))

    # Get the coordinator
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator: ZoneHeaterManagerCoordinator = hass.data[DOMAIN][entry_id]
    
    # Subscribe to coordinator updates
    unsub = coordinator.async_add_listener(forward_messages)
    
    @callback
    def unsub_callback():
        """Unsubscribe from updates."""
        unsub()
    
    connection.subscriptions[msg["id"]] = unsub_callback
    connection.send_result(msg["id"])


@websocket_command({
    "type": "zone_heater_manager/get_zones",
})
@callback
def websocket_get_zones(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all zones via websocket.
    
    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator: ZoneHeaterManagerCoordinator = hass.data[DOMAIN][entry_id]
    zone_manager = coordinator.zone_manager
    
    zones = zone_manager.get_all_zones()
    zones_data = []
    
    for zone_id, zone in zones.items():
        zones_data.append({
            "id": zone.zone_id,
            "name": zone.name,
            "enabled": zone.enabled,
            "state": zone.state,
            "target_temperature": zone.target_temperature,
            "current_temperature": zone.current_temperature,
            "devices": [
                {
                    "id": dev_id,
                    "type": dev_data["type"],
                    "mqtt_topic": dev_data.get("mqtt_topic"),
                }
                for dev_id, dev_data in zone.devices.items()
            ],
        })
    
    connection.send_result(msg["id"], {"zones": zones_data})


@websocket_command({
    "type": "zone_heater_manager/create_zone",
    "zone_id": str,
    "zone_name": str,
    "temperature": float,
})
@callback
def websocket_create_zone(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Create a zone via websocket.
    
    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: Message data
    """
    entry_id = list(hass.data[DOMAIN].keys())[0]
    coordinator: ZoneHeaterManagerCoordinator = hass.data[DOMAIN][entry_id]
    zone_manager = coordinator.zone_manager
    
    try:
        zone = zone_manager.create_zone(
            msg["zone_id"],
            msg["zone_name"],
            msg.get("temperature", 20.0)
        )
        
        hass.async_create_task(zone_manager.async_save())
        hass.async_create_task(coordinator.async_request_refresh())
        
        connection.send_result(msg["id"], {
            "success": True,
            "zone": {
                "id": zone.zone_id,
                "name": zone.name,
                "target_temperature": zone.target_temperature,
            }
        })
    except ValueError as err:
        connection.send_error(msg["id"], "creation_failed", str(err))


async def setup_websocket(hass: HomeAssistant) -> None:
    """Set up WebSocket API.
    
    Args:
        hass: Home Assistant instance
    """
    async_register_command(hass, websocket_subscribe_updates)
    async_register_command(hass, websocket_get_zones)
    async_register_command(hass, websocket_create_zone)
    
    _LOGGER.info("Zone Heater Manager WebSocket API registered")
