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
    _LOGGER.debug("WebSocket subscribe called")
    
    @callback
    def forward_messages():
        """Forward coordinator updates to websocket."""
        area_count = len(coordinator.data.get("areas", {})) if coordinator.data else 0
        _LOGGER.debug(
            "WebSocket: Sending update to client (areas: %d)",
            area_count
        )
        if coordinator.data and "areas" in coordinator.data:
            for area_id, area_data in coordinator.data["areas"].items():
                _LOGGER.debug(
                    "  Area %s: manual_override=%s, target_temp=%s",
                    area_id,
                    area_data.get("manual_override", "NOT SET"),
                    area_data.get("target_temperature")
                )
        connection.send_message(result_message(msg["id"], {
            "event": "update",
            "data": coordinator.data
        }))

    # Get the coordinator - filter out non-entry keys
    entry_ids = [
        key for key in hass.data[DOMAIN].keys()
        if key not in ["history", "climate_controller", "schedule_executor", "learning_engine", "area_logger", "vacation_manager"]
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
        if key not in ["history", "climate_controller", "schedule_executor", "learning_engine", "area_logger", "vacation_manager"]
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
        # Get device states
        devices_data = []
        for dev_id, dev_data in area.devices.items():
            state = hass.states.get(dev_id)
            device_info = {
                "id": dev_id,
                "type": dev_data["type"],
                "mqtt_topic": dev_data.get("mqtt_topic"),
                "state": state.state if state else "unavailable",
            }
            
            # Add device-specific attributes
            if state and state.attributes:
                if dev_data["type"] == "thermostat":
                    device_info["current_temperature"] = state.attributes.get("current_temperature")
                    device_info["target_temperature"] = state.attributes.get("temperature")
                    device_info["hvac_action"] = state.attributes.get("hvac_action")
                    device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
                elif dev_data["type"] == "temperature_sensor":
                    device_info["temperature"] = state.attributes.get("temperature", state.state)
                    device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
                elif dev_data["type"] == "valve":
                    device_info["position"] = state.attributes.get("position")
                    device_info["friendly_name"] = state.attributes.get("friendly_name", dev_id)
            
            devices_data.append(device_info)
        
        areas_data.append({
            "id": area.area_id,
            "name": area.name,
            "enabled": area.enabled,
            "state": area.state,
            "target_temperature": area.target_temperature,
            "current_temperature": area.current_temperature,
            "devices": devices_data,
            "schedules": [s.to_dict() for s in area.schedules.values()],
            # Night boost
            "night_boost_enabled": area.night_boost_enabled,
            "night_boost_offset": area.night_boost_offset,
            "night_boost_start_time": area.night_boost_start_time,
            "night_boost_end_time": area.night_boost_end_time,
            # Smart night boost
            "smart_night_boost_enabled": area.smart_night_boost_enabled,
            "smart_night_boost_target_time": area.smart_night_boost_target_time,
            "weather_entity_id": area.weather_entity_id,
            # Preset modes
            "preset_mode": area.preset_mode,
            "away_temp": area.away_temp,
            "eco_temp": area.eco_temp,
            "comfort_temp": area.comfort_temp,
            "home_temp": area.home_temp,
            "sleep_temp": area.sleep_temp,
            "activity_temp": area.activity_temp,
            # Boost mode
            "boost_mode_active": area.boost_mode_active,
            "boost_temp": area.boost_temp,
            "boost_duration": area.boost_duration,
            # HVAC mode
            "hvac_mode": area.hvac_mode,
            # Sensors
            "window_sensors": area.window_sensors,
            "presence_sensors": area.presence_sensors,
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
