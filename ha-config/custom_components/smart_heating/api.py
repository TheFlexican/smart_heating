"""Flask API server for Smart Heating."""
import logging
from typing import Any

from aiohttp import web
import aiohttp_cors

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class ZoneHeaterAPIView(HomeAssistantView):
    """API view for Smart Heating."""

    url = "/api/smart_heating/{endpoint:.*}"
    name = "api:smart_heating"
    requires_auth = True

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager) -> None:
        """Initialize the API view.
        
        Args:
            hass: Home Assistant instance
            area_manager: Zone manager instance
        """
        self.hass = hass
        self.area_manager = area_manager

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
                area_id = endpoint.split("/")[1]
                return await self.get_area(request, area_id)
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
                return await self.create_area(request, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/devices"):
                area_id = endpoint.split("/")[1]
                return await self.add_device(request, area_id, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/temperature"):
                area_id = endpoint.split("/")[1]
                return await self.set_temperature(request, area_id, data)
            elif endpoint.startswith("zones/") and endpoint.endswith("/enable"):
                area_id = endpoint.split("/")[1]
                return await self.enable_area(request, area_id)
            elif endpoint.startswith("zones/") and endpoint.endswith("/disable"):
                area_id = endpoint.split("/")[1]
                return await self.disable_area(request, area_id)
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
                area_id = parts[1]
                device_id = parts[3]
                return await self.remove_device(request, area_id, device_id)
            elif endpoint.startswith("zones/"):
                area_id = endpoint.split("/")[1]
                return await self.delete_area(request, area_id)
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
        zones = self.area_manager.get_all_areas()
        zones_data = []
        
        for area_id, area in zones.items():
            zones_data.append({
                "id": zone.area_id,
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

    async def get_zone(self, request: web.Request, area_id: str) -> web.Response:
        """Get a specific zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response with zone data
        """
        zone = self.area_manager.get_area(area_id)
        
        if zone is None:
            return web.json_response(
                {"error": f"Zone {area_id} not found"}, status=404
            )
        
        zone_data = {
            "id": zone.area_id,
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
        
        return web.json_response(area_data)

    async def get_devices(self, request: web.Request) -> web.Response:
        """Get available Zigbee2MQTT devices.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with available devices
        """
        devices = []
        
        # Get all MQTT entities from Home Assistant
        entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)
        
        # Find entities that are from MQTT and could be heating-related
        heating_platforms = ["climate", "sensor", "number", "switch"]
        
        for entity in entity_registry.entities.values():
            # Check if entity is from MQTT integration
            if entity.platform == "mqtt":
                # Get entity state for additional info
                state = self.hass.states.get(entity.entity_id)
                if not state:
                    continue
                
                # Determine device type based on entity domain and attributes
                device_type = "temperature_sensor"  # default
                
                if entity.domain == "climate":
                    device_type = "thermostat"
                elif entity.domain == "sensor":
                    # Check if it's a temperature sensor
                    unit = state.attributes.get("unit_of_measurement", "")
                    if "°C" in unit or "°F" in unit or "temperature" in entity.entity_id.lower():
                        device_type = "temperature_sensor"
                    else:
                        continue  # Skip non-temperature sensors
                elif entity.domain == "number" and "valve" in entity.entity_id.lower():
                    device_type = "valve"
                elif entity.domain == "switch" and any(keyword in entity.entity_id.lower() 
                                                       for keyword in ["thermostat", "heater", "radiator"]):
                    device_type = "thermostat"
                else:
                    # Skip entities that don't match heating domains
                    if entity.domain not in heating_platforms:
                        continue
                
                # Check if device is already assigned to a zone
                assigned_zones = []
                for area_id, area in self.area_manager.get_all_areas().items():
                    if entity.entity_id in zone.devices:
                        assigned_zones.append(area_id)
                
                devices.append({
                    "id": entity.entity_id,
                    "name": state.attributes.get("friendly_name", entity.entity_id),
                    "type": device_type,
                    "entity_id": entity.entity_id,
                    "domain": entity.domain,
                    "assigned_zones": assigned_zones,
                    "state": state.state,
                    "attributes": {
                        "temperature": state.attributes.get("temperature"),
                        "current_temperature": state.attributes.get("current_temperature"),
                        "unit_of_measurement": state.attributes.get("unit_of_measurement"),
                    }
                })
        
        return web.json_response({"devices": devices})

    async def get_status(self, request: web.Request) -> web.Response:
        """Get system status.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with status
        """
        zones = self.area_manager.get_all_areas()
        
        status = {
            "zone_count": len(areas),
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
        area_id = data.get("area_id")
        zone_name = data.get("zone_name")
        temperature = data.get("temperature", 20.0)
        
        if not area_id or not zone_name:
            return web.json_response(
                {"error": "area_id and zone_name are required"}, status=400
            )
        
        try:
            zone = self.area_manager.create_area(area_id, area_name, temperature)
            await self.area_manager.async_save()
            
            return web.json_response({
                "success": True,
                "zone": {
                    "id": zone.area_id,
                    "name": zone.name,
                    "target_temperature": zone.target_temperature,
                }
            })
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def delete_zone(self, request: web.Request, area_id: str) -> web.Response:
        """Delete a zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.delete_area(area_id)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def add_device(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add a device to a zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
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
            self.area_manager.add_device_to_area(
                area_id, device_id, device_type, mqtt_topic
            )
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def remove_device(
        self, request: web.Request, area_id: str, device_id: str
    ) -> web.Response:
        """Remove a device from a zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
            device_id: Device identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.remove_device_from_area(area_id, device_id)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def set_temperature(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Set zone temperature.
        
        Args:
            request: Request object
            area_id: Zone identifier
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
            self.area_manager.set_area_target_temperature(area_id, temperature)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def enable_zone(self, request: web.Request, area_id: str) -> web.Response:
        """Enable a zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.enable_area(area_id)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def disable_zone(self, request: web.Request, area_id: str) -> web.Response:
        """Disable a zone.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.disable_area(area_id)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )


async def setup_api(hass: HomeAssistant, area_manager: AreaManager) -> None:
    """Set up the API.
    
    Args:
        hass: Home Assistant instance
        area_manager: Zone manager instance
    """
    view = ZoneHeaterAPIView(hass, area_manager)
    hass.http.register_view(view)
    
    _LOGGER.info("Smart Heating API registered")
