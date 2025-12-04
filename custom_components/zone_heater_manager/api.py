"""Flask API server for Zone Heater Manager."""
import logging
from typing import Any

from aiohttp import web
import aiohttp_cors

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .zone_manager import ZoneManager

_LOGGER = logging.getLogger(__name__)


class ZoneHeaterAPIView(HomeAssistantView):
    """API view for Zone Heater Manager."""

    url = "/api/zone_heater_manager/{endpoint:.*}"
    name = "api:zone_heater_manager"
    requires_auth = True

    def __init__(self, hass: HomeAssistant, zone_manager: ZoneManager) -> None:
        """Initialize the API view.
        
        Args:
            hass: Home Assistant instance
            zone_manager: Zone manager instance
        """
        self.hass = hass
        self.zone_manager = zone_manager

    async def get(self, request: web.Request, endpoint: str) -> web.Response:
        """Handle GET requests.
        
        Args:
            request: Request object
            endpoint: API endpoint
            
        Returns:
            JSON response
        """
        try:
            if endpoint == "zones":
                return await self.get_zones(request)
            elif endpoint.startswith("zones/"):
                zone_id = endpoint.split("/")[1]
                return await self.get_zone(request, zone_id)
            elif endpoint == "devices":
                return await self.get_devices(request)
            elif endpoint == "status":
                return await self.get_status(request)
            else:
                return web.json_response(
                    {"error": "Unknown endpoint"}, status=404
                )
        except Exception as err:
            _LOGGER.error("Error handling GET %s: %s", endpoint, err)
            return web.json_response(
                {"error": str(err)}, status=500
            )

    async def post(self, request: web.Request, endpoint: str) -> web.Response:
        """Handle POST requests.
        
        Args:
            request: Request object
            endpoint: API endpoint
            
        Returns:
            JSON response
        """
        try:
            data = await request.json()
            
            if endpoint == "zones":
                return await self.create_zone(request, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/devices"):
                zone_id = endpoint.split("/")[1]
                return await self.add_device(request, zone_id, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/temperature"):
                zone_id = endpoint.split("/")[1]
                return await self.set_temperature(request, zone_id, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/enable"):
                zone_id = endpoint.split("/")[1]
                return await self.enable_zone(request, zone_id)
            elif endpoint.startswith("zones/") and endpoint.endswith("/disable"):
                zone_id = endpoint.split("/")[1]
                return await self.disable_zone(request, zone_id)
            else:
                return web.json_response(
                    {"error": "Unknown endpoint"}, status=404
                )
        except Exception as err:
            _LOGGER.error("Error handling POST %s: %s", endpoint, err)
            return web.json_response(
                {"error": str(err)}, status=500
            )

    async def delete(self, request: web.Request, endpoint: str) -> web.Response:
        """Handle DELETE requests.
        
        Args:
            request: Request object
            endpoint: API endpoint
            
        Returns:
            JSON response
        """
        try:
            if endpoint.startswith("zones/") and "/devices/" in endpoint:
                parts = endpoint.split("/")
                zone_id = parts[1]
                device_id = parts[3]
                return await self.remove_device(request, zone_id, device_id)
            elif endpoint.startswith("zones/"):
                zone_id = endpoint.split("/")[1]
                return await self.delete_zone(request, zone_id)
            else:
                return web.json_response(
                    {"error": "Unknown endpoint"}, status=404
                )
        except Exception as err:
            _LOGGER.error("Error handling DELETE %s: %s", endpoint, err)
            return web.json_response(
                {"error": str(err)}, status=500
            )

    async def get_zones(self, request: web.Request) -> web.Response:
        """Get all zones.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with zones
        """
        zones = self.zone_manager.get_all_zones()
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
        
        return web.json_response({"zones": zones_data})

    async def get_zone(self, request: web.Request, zone_id: str) -> web.Response:
        """Get a specific zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            
        Returns:
            JSON response with zone data
        """
        zone = self.zone_manager.get_zone(zone_id)
        
        if zone is None:
            return web.json_response(
                {"error": f"Zone {zone_id} not found"}, status=404
            )
        
        zone_data = {
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
        }
        
        return web.json_response(zone_data)

    async def get_devices(self, request: web.Request) -> web.Response:
        """Get available Zigbee2MQTT devices.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with available devices
        """
        # TODO: Implement MQTT device discovery
        # For now, return empty list
        devices = []
        
        return web.json_response({"devices": devices})

    async def get_status(self, request: web.Request) -> web.Response:
        """Get system status.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with status
        """
        zones = self.zone_manager.get_all_zones()
        
        status = {
            "zone_count": len(zones),
            "active_zones": sum(1 for z in zones.values() if z.enabled),
            "total_devices": sum(len(z.devices) for z in zones.values()),
        }
        
        return web.json_response(status)

    async def create_zone(self, request: web.Request, data: dict) -> web.Response:
        """Create a new zone.
        
        Args:
            request: Request object
            data: Zone data
            
        Returns:
            JSON response
        """
        zone_id = data.get("zone_id")
        zone_name = data.get("zone_name")
        temperature = data.get("temperature", 20.0)
        
        if not zone_id or not zone_name:
            return web.json_response(
                {"error": "zone_id and zone_name are required"}, status=400
            )
        
        try:
            zone = self.zone_manager.create_zone(zone_id, zone_name, temperature)
            await self.zone_manager.async_save()
            
            return web.json_response({
                "success": True,
                "zone": {
                    "id": zone.zone_id,
                    "name": zone.name,
                    "target_temperature": zone.target_temperature,
                }
            })
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def delete_zone(self, request: web.Request, zone_id: str) -> web.Response:
        """Delete a zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.zone_manager.delete_zone(zone_id)
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def add_device(
        self, request: web.Request, zone_id: str, data: dict
    ) -> web.Response:
        """Add a device to a zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
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
            self.zone_manager.add_device_to_zone(
                zone_id, device_id, device_type, mqtt_topic
            )
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def remove_device(
        self, request: web.Request, zone_id: str, device_id: str
    ) -> web.Response:
        """Remove a device from a zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            device_id: Device identifier
            
        Returns:
            JSON response
        """
        try:
            self.zone_manager.remove_device_from_zone(zone_id, device_id)
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def set_temperature(
        self, request: web.Request, zone_id: str, data: dict
    ) -> web.Response:
        """Set zone temperature.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            data: Temperature data
            
        Returns:
            JSON response
        """
        temperature = data.get("temperature")
        
        if temperature is None:
            return web.json_response(
                {"error": "temperature is required"}, status=400
            )
        
        try:
            self.zone_manager.set_zone_target_temperature(zone_id, temperature)
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def enable_zone(self, request: web.Request, zone_id: str) -> web.Response:
        """Enable a zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.zone_manager.enable_zone(zone_id)
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def disable_zone(self, request: web.Request, zone_id: str) -> web.Response:
        """Disable a zone.
        
        Args:
            request: Request object
            zone_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.zone_manager.disable_zone(zone_id)
            await self.zone_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )


async def setup_api(hass: HomeAssistant, zone_manager: ZoneManager) -> None:
    """Set up the API.
    
    Args:
        hass: Home Assistant instance
        zone_manager: Zone manager instance
    """
    view = ZoneHeaterAPIView(hass, zone_manager)
    hass.http.register_view(view)
    
    _LOGGER.info("Zone Heater Manager API registered")
