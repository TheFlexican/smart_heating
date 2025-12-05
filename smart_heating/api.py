"""Flask API server for Smart Heating."""
import logging
from typing import Any

from aiohttp import web
import aiohttp_cors
import aiofiles

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, area_registry as ar, device_registry as dr

from .const import DOMAIN
from .area_manager import AreaManager, Area

_LOGGER = logging.getLogger(__name__)


class SmartHeatingAPIView(HomeAssistantView):
    """API view for Smart Heating."""

    url = "/api/smart_heating/{endpoint:.*}"
    name = "api:smart_heating"
    requires_auth = False

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
            if endpoint == "areas":
                return await self.get_areas(request)
            elif endpoint == "devices":
                return await self.get_devices(request)
            elif endpoint == "status":
                return await self.get_status(request)
            elif endpoint == "config":
                return await self.get_config(request)
            elif endpoint == "history/config":
                return await self.get_history_config(request)
            elif endpoint == "entities/binary_sensor":
                return await self.get_binary_sensor_entities(request)
            elif endpoint.startswith("entity_state/"):
                entity_id = endpoint.replace("entity_state/", "")
                return await self.get_entity_state(request, entity_id)
            elif endpoint.startswith("areas/") and "/history" in endpoint:
                area_id = endpoint.split("/")[1]
                return await self.get_history(request, area_id)
            elif endpoint.startswith("areas/") and "/learning" in endpoint:
                area_id = endpoint.split("/")[1]
                return await self.get_learning_stats(request, area_id)
            elif endpoint.startswith("areas/"):
                area_id = endpoint.split("/")[1]
                return await self.get_area(request, area_id)
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
            _LOGGER.debug("POST request to endpoint: %s", endpoint)
            
            # Handle endpoints that don't require a body first
            if endpoint.startswith("areas/") and endpoint.endswith("/enable"):
                area_id = endpoint.split("/")[1]
                return await self.enable_area(request, area_id)
            elif endpoint.startswith("areas/") and endpoint.endswith("/disable"):
                area_id = endpoint.split("/")[1]
                return await self.disable_area(request, area_id)
            elif endpoint.startswith("areas/") and endpoint.endswith("/hide"):
                area_id = endpoint.split("/")[1]
                return await self.hide_area(request, area_id)
            elif endpoint.startswith("areas/") and endpoint.endswith("/unhide"):
                area_id = endpoint.split("/")[1]
                return await self.unhide_area(request, area_id)
            elif endpoint.startswith("areas/") and endpoint.endswith("/cancel_boost"):
                area_id = endpoint.split("/")[1]
                return await self.cancel_boost(request, area_id)
            
            # Parse JSON for endpoints that need it
            data = await request.json()
            _LOGGER.debug("POST data: %s", data)
            
            if endpoint.startswith("areas/") and endpoint.endswith("/devices"):
                area_id = endpoint.split("/")[1]
                return await self.add_device(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/schedules"):
                area_id = endpoint.split("/")[1]
                return await self.add_schedule(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/temperature"):
                area_id = endpoint.split("/")[1]
                return await self.set_temperature(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/preset_mode"):
                area_id = endpoint.split("/")[1]
                return await self.set_preset_mode(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/boost"):
                area_id = endpoint.split("/")[1]
                return await self.set_boost_mode(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/boost"):
                area_id = endpoint.split("/")[1]
                return await self.set_boost_mode(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/window_sensors"):
                area_id = endpoint.split("/")[1]
                return await self.add_window_sensor(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/presence_sensors"):
                area_id = endpoint.split("/")[1]
                return await self.add_presence_sensor(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/hvac_mode"):
                area_id = endpoint.split("/")[1]
                return await self.set_hvac_mode(request, area_id, data)
            elif endpoint == "frost_protection":
                return await self.set_frost_protection(request, data)
            elif endpoint == "history/config":
                return await self.set_history_config(request, data)
            elif endpoint == "call_service":
                return await self.call_service(request, data)
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
            if endpoint.startswith("areas/") and "/devices/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                device_id = parts[3]
                return await self.remove_device(request, area_id, device_id)
            elif endpoint.startswith("areas/") and "/schedules/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                schedule_id = parts[3]
                return await self.remove_schedule(request, area_id, schedule_id)
            elif endpoint.startswith("areas/") and "/window_sensors/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await self.remove_window_sensor(request, area_id, entity_id)
            elif endpoint.startswith("areas/") and "/presence_sensors/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await self.remove_presence_sensor(request, area_id, entity_id)
            else:
                return web.json_response(
                    {"error": "Unknown endpoint"}, status=404
                )
        except Exception as err:
            _LOGGER.error("Error handling DELETE %s: %s", endpoint, err)
            return web.json_response(
                {"error": str(err)}, status=500
            )

    async def get_areas(self, request: web.Request) -> web.Response:
        """Get all Home Assistant areas.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with HA areas
        """
        # Get Home Assistant's area registry
        area_registry = ar.async_get(self.hass)
        
        areas_data = []
        for area in area_registry.areas.values():
            area_id = area.id
            area_name = area.name
            
            # Check if we have stored data for this area
            stored_area = self.area_manager.get_area(area_id)
            
            if stored_area:
                # Use stored data
                devices_list = []
                
                # Get coordinator data for device states
                # The coordinator is stored under the entry_id, find it
                coordinator = None
                for key, value in self.hass.data[DOMAIN].items():
                    if hasattr(value, 'data') and hasattr(value, 'async_request_refresh'):
                        coordinator = value
                        break
                
                coordinator_devices = {}
                if coordinator and coordinator.data and "areas" in coordinator.data:
                    area_data = coordinator.data["areas"].get(area_id, {})
                    for device in area_data.get("devices", []):
                        coordinator_devices[device["id"]] = device
                
                for dev_id, dev_data in stored_area.devices.items():
                    device_info = {
                        "id": dev_id,
                        "type": dev_data["type"],
                        "mqtt_topic": dev_data.get("mqtt_topic"),
                    }
                    # Get friendly name from entity state
                    state = self.hass.states.get(dev_id)
                    if state:
                        device_info["name"] = state.attributes.get("friendly_name", dev_id)
                    
                    # Add coordinator data if available
                    if dev_id in coordinator_devices:
                        coord_device = coordinator_devices[dev_id]
                        device_info["state"] = coord_device.get("state")
                        device_info["current_temperature"] = coord_device.get("current_temperature")
                        device_info["target_temperature"] = coord_device.get("target_temperature")
                        device_info["hvac_action"] = coord_device.get("hvac_action")
                        device_info["temperature"] = coord_device.get("temperature")
                        device_info["position"] = coord_device.get("position")
                    
                    devices_list.append(device_info)
                
                areas_data.append({
                    "id": area_id,
                    "name": area_name,
                    "enabled": stored_area.enabled,
                    "hidden": stored_area.hidden,
                    "state": stored_area.state,
                    "target_temperature": stored_area.target_temperature,
                    "current_temperature": stored_area.current_temperature,
                    "devices": devices_list,
                    "schedules": [s.to_dict() for s in stored_area.schedules.values()],
                    # Night boost
                    "night_boost_enabled": stored_area.night_boost_enabled,
                    "night_boost_offset": stored_area.night_boost_offset,
                    "night_boost_start_time": stored_area.night_boost_start_time,
                    "night_boost_end_time": stored_area.night_boost_end_time,
                    # Smart night boost
                    "smart_night_boost_enabled": stored_area.smart_night_boost_enabled,
                    "smart_night_boost_target_time": stored_area.smart_night_boost_target_time,
                    "weather_entity_id": stored_area.weather_entity_id,
                    # Preset modes
                    "preset_mode": stored_area.preset_mode,
                    "away_temp": stored_area.away_temp,
                    "eco_temp": stored_area.eco_temp,
                    "comfort_temp": stored_area.comfort_temp,
                    "home_temp": stored_area.home_temp,
                    "sleep_temp": stored_area.sleep_temp,
                    "activity_temp": stored_area.activity_temp,
                    # Boost mode
                    "boost_mode_active": stored_area.boost_mode_active,
                    "boost_temp": stored_area.boost_temp,
                    "boost_duration": stored_area.boost_duration,
                    # HVAC mode
                    "hvac_mode": stored_area.hvac_mode,
                    # Sensors
                    "window_sensors": stored_area.window_sensors,
                    "presence_sensors": stored_area.presence_sensors,
                })
            else:
                # Default data for HA area without stored settings
                areas_data.append({
                    "id": area_id,
                    "name": area_name,
                    "enabled": True,
                    "hidden": False,
                    "state": "idle",
                    "target_temperature": 20.0,
                    "current_temperature": None,
                    "devices": [],
                    "schedules": [],
                })
        
        return web.json_response({"areas": areas_data})

    async def get_area(self, request: web.Request, area_id: str) -> web.Response:
        """Get a specific area.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response with area data
        """
        area = self.area_manager.get_area(area_id)
        
        if area is None:
            return web.json_response(
                {"error": f"Zone {area_id} not found"}, status=404
            )
        
        devices_list = []
        for dev_id, dev_data in area.devices.items():
            device_info = {
                "id": dev_id,
                "type": dev_data["type"],
                "mqtt_topic": dev_data.get("mqtt_topic"),
            }
            # Get friendly name from entity state
            state = self.hass.states.get(dev_id)
            if state:
                device_info["name"] = state.attributes.get("friendly_name", dev_id)
            devices_list.append(device_info)
        
        area_data = {
            "id": area.area_id,
            "name": area.name,
            "enabled": area.enabled,
            "state": area.state,
            "target_temperature": area.target_temperature,
            "current_temperature": area.current_temperature,
            "devices": devices_list,
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
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)
        area_registry = ar.async_get(self.hass)
        
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
                device_type = None
                device_class = state.attributes.get("device_class")
                
                if entity.domain == "climate":
                    device_type = "thermostat"
                elif entity.domain == "sensor":
                    # Use device_class if available
                    if device_class == "temperature":
                        device_type = "temperature_sensor"
                    else:
                        # Fallback to unit check
                        unit = state.attributes.get("unit_of_measurement", "")
                        if "°C" in unit or "°F" in unit or "temperature" in entity.entity_id.lower():
                            device_type = "temperature_sensor"
                        else:
                            continue  # Skip non-temperature sensors
                elif entity.domain == "switch":
                    # Only include switches that are heating-related
                    if any(keyword in entity.entity_id.lower() 
                           for keyword in ["thermostat", "heater", "radiator", "heating"]):
                        device_type = "thermostat"
                    else:
                        continue  # Skip non-heating switches
                elif entity.domain == "number":
                    if "valve" in entity.entity_id.lower() or device_class == "valve":
                        device_type = "valve"
                    else:
                        continue
                else:
                    # Skip entities that don't match heating domains
                    continue
                
                # Skip if device type couldn't be determined
                if not device_type:
                    continue
                
                # Check if device is already assigned to a area
                assigned_areas = []
                for area_id, area in self.area_manager.get_all_areas().items():
                    if entity.entity_id in area.devices:
                        assigned_areas.append(area_id)
                
                # Get Home Assistant area for this entity
                ha_area_id = None
                ha_area_name = None
                if entity.device_id:
                    device_entry = device_registry.async_get(entity.device_id)
                    if device_entry and device_entry.area_id:
                        area_entry = area_registry.async_get_area(device_entry.area_id)
                        if area_entry:
                            ha_area_id = area_entry.id
                            ha_area_name = area_entry.name
                
                devices.append({
                    "id": entity.entity_id,
                    "name": state.attributes.get("friendly_name", entity.entity_id),
                    "type": device_type,
                    "entity_id": entity.entity_id,
                    "domain": entity.domain,
                    "assigned_areas": assigned_areas,
                    "ha_area_id": ha_area_id,
                    "ha_area_name": ha_area_name,
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
        areas = self.area_manager.get_all_areas()
        
        status = {
            "area_count": len(areas),
            "active_areas": sum(1 for z in areas.values() if z.enabled),
            "total_devices": sum(len(z.devices) for z in areas.values()),
        }
        
        return web.json_response(status)

    async def get_config(self, request: web.Request) -> web.Response:
        """Get system configuration.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with configuration
        """
        config = {
            "opentherm_gateway_id": self.area_manager.opentherm_gateway_id,
            "opentherm_enabled": self.area_manager.opentherm_enabled,
            "trv_heating_temp": self.area_manager.trv_heating_temp,
            "trv_idle_temp": self.area_manager.trv_idle_temp,
            "trv_temp_offset": self.area_manager.trv_temp_offset,
        }
        
        return web.json_response(config)

    async def get_entity_state(self, request: web.Request, entity_id: str) -> web.Response:
        """Get entity state from Home Assistant.
        
        Args:
            request: Request object
            entity_id: Entity ID to fetch
            
        Returns:
            JSON response with entity state
        """
        state = self.hass.states.get(entity_id)
        
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

    async def get_binary_sensor_entities(self, request: web.Request) -> web.Response:
        """Get all binary sensor entities from Home Assistant.
        
        Also includes person and device_tracker entities for presence detection.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with list of binary sensor entities
        """
        entities = []
        
        # Get binary sensors
        for entity_id in self.hass.states.async_entity_ids("binary_sensor"):
            state = self.hass.states.get(entity_id)
            if state:
                entities.append({
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": state.attributes.get("device_class"),
                    }
                })
        
        # Get person entities (for presence detection)
        for entity_id in self.hass.states.async_entity_ids("person"):
            state = self.hass.states.get(entity_id)
            if state:
                entities.append({
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    }
                })
        
        # Get device_tracker entities (for presence detection)
        for entity_id in self.hass.states.async_entity_ids("device_tracker"):
            state = self.hass.states.get(entity_id)
            if state:
                entities.append({
                    "entity_id": entity_id,
                    "state": state.state,
                    "attributes": {
                        "friendly_name": state.attributes.get("friendly_name", entity_id),
                        "device_class": "presence",  # Virtual device class for filtering
                    }
                })
        
        return web.json_response({"entities": entities})

    async def add_device(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add a device to a area.
        
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
            # Ensure area exists in storage
            if self.area_manager.get_area(area_id) is None:
                # Auto-create area entry for this HA area if not exists
                area_registry = ar.async_get(self.hass)
                ha_area = area_registry.async_get_area(area_id)
                if ha_area:
                    # Create internal storage for this HA area
                    area = Area(area_id, ha_area.name)
                    self.area_manager.areas[area_id] = area
                else:
                    return web.json_response(
                        {"error": f"Area {area_id} not found"}, status=404
                    )
            
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
        """Remove a device from a area.
        
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
        """Set area temperature.
        
        Args:
            request: Request object
            area_id: Zone identifier
            data: Temperature data
            
        Returns:
            JSON response
        """
        _LOGGER.debug("set_temperature called for area_id: %s", area_id)
        temperature = data.get("temperature")
        
        if temperature is None:
            return web.json_response(
                {"error": "temperature is required"}, status=400
            )
        
        try:
            _LOGGER.debug("Setting temperature for area %s to %s", area_id, temperature)
            self.area_manager.set_area_target_temperature(area_id, temperature)
            await self.area_manager.async_save()
            
            # Trigger immediate climate control to update devices
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
                _LOGGER.info("Triggered immediate climate control after temperature change")
            
            # Refresh coordinator to notify websocket listeners
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
                _LOGGER.debug("Coordinator refreshed to update frontend")
            
            return web.json_response({"success": True})
        except ValueError as err:
            _LOGGER.error("ValueError setting temperature for area %s: %s", area_id, err)
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def enable_area(self, request: web.Request, area_id: str) -> web.Response:
        """Enable a area.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.enable_area(area_id)
            await self.area_manager.async_save()
            
            # Trigger immediate climate control
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def disable_area(self, request: web.Request, area_id: str) -> web.Response:
        """Disable a area.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.disable_area(area_id)
            await self.area_manager.async_save()
            
            # Trigger immediate climate control to turn off devices
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )
    
    async def hide_area(self, request: web.Request, area_id: str) -> web.Response:
        """Hide an area from main view.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                # Area doesn't exist in storage yet - create it
                # Get area name from HA registry
                area_registry = ar.async_get(self.hass)
                ha_area = area_registry.async_get_area(area_id)
                if not ha_area:
                    return web.json_response(
                        {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                    )
                
                # Import Area class
                from .area_manager import Area
                
                # Create area with default settings
                area = Area(
                    area_id=area_id,
                    name=ha_area.name,
                    target_temperature=20.0,
                    enabled=True
                )
                self.area_manager.areas[area_id] = area
            
            area.hidden = True
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except Exception as err:
            return web.json_response(
                {"error": str(err)}, status=500
            )
    
    async def unhide_area(self, request: web.Request, area_id: str) -> web.Response:
        """Unhide an area to show in main view.
        
        Args:
            request: Request object
            area_id: Zone identifier
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                # Area doesn't exist in storage yet - create it
                # Get area name from HA registry
                area_registry = ar.async_get(self.hass)
                ha_area = area_registry.async_get_area(area_id)
                if not ha_area:
                    return web.json_response(
                        {"error": f"Area {area_id} not found in Home Assistant"}, status=404
                    )
                
                # Import Area class
                from .area_manager import Area
                
                # Create area with default settings
                area = Area(
                    area_id=area_id,
                    name=ha_area.name,
                    target_temperature=20.0,
                    enabled=True
                )
                self.area_manager.areas[area_id] = area
            
            area.hidden = False
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except Exception as err:
            return web.json_response(
                {"error": str(err)}, status=500
            )
    
    async def call_service(self, request: web.Request, data: dict) -> web.Response:
        """Call a Home Assistant service.
        
        Args:
            request: Request object
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
            
            await self.hass.services.async_call(
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
    
    async def get_history(self, request: web.Request, area_id: str) -> web.Response:
        """Get temperature history for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            
        Returns:
            JSON response with history
        """
        from .const import DOMAIN
        from datetime import datetime
        
        # Get query parameters
        hours = request.query.get("hours")
        start_time = request.query.get("start_time")
        end_time = request.query.get("end_time")
        
        history_tracker = self.hass.data.get(DOMAIN, {}).get("history")
        if not history_tracker:
            return web.json_response(
                {"error": "History not available"}, status=503
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

    async def get_learning_stats(self, request: web.Request, area_id: str) -> web.Response:
        """Get learning statistics for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            
        Returns:
            JSON response with learning stats
        """
        from .const import DOMAIN
        
        learning_engine = self.hass.data.get(DOMAIN, {}).get("learning_engine")
        if not learning_engine:
            return web.json_response(
                {"error": "Learning engine not available"}, status=503
            )
        
        stats = await learning_engine.async_get_learning_stats(area_id)
        
        return web.json_response({
            "area_id": area_id,
            "stats": stats
        })

    async def add_schedule(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add schedule to an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Schedule data (day, start_time, end_time, temperature)
            
        Returns:
            JSON response
        """
        import uuid
        
        schedule_id = data.get("id") or str(uuid.uuid4())
        temperature = data.get("temperature")
        
        if temperature is None:
            return web.json_response(
                {"error": "temperature is required"}, status=400
            )
        
        try:
            # Ensure area exists in storage
            if self.area_manager.get_area(area_id) is None:
                # Auto-create area entry for this HA area if not exists
                area_registry = ar.async_get(self.hass)
                ha_area = area_registry.async_get_area(area_id)
                if ha_area:
                    # Create internal storage for this HA area
                    area = Area(area_id, ha_area.name)
                    self.area_manager.areas[area_id] = area
                else:
                    return web.json_response(
                        {"error": f"Area {area_id} not found"}, status=404
                    )
            
            # Create schedule from frontend data
            from .area_manager import Schedule
            schedule = Schedule(
                schedule_id=schedule_id,
                time=data.get("time"),
                temperature=temperature,
                days=data.get("days"),
                enabled=data.get("enabled", True),
                day=data.get("day"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
            )
            
            area = self.area_manager.get_area(area_id)
            area.add_schedule(schedule)
            await self.area_manager.async_save()
            
            return web.json_response({
                "success": True,
                "schedule": schedule.to_dict()
            })
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def remove_schedule(
        self, request: web.Request, area_id: str, schedule_id: str
    ) -> web.Response:
        """Remove schedule from an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            schedule_id: Schedule identifier
            
        Returns:
            JSON response
        """
        try:
            self.area_manager.remove_schedule_from_area(area_id, schedule_id)
            await self.area_manager.async_save()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def set_preset_mode(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Set preset mode for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with preset_mode
            
        Returns:
            JSON response
        """
        preset_mode = data.get("preset_mode")
        if not preset_mode:
            return web.json_response(
                {"error": "preset_mode required"}, status=400
            )
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.set_preset_mode(preset_mode)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "preset_mode": preset_mode})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def set_boost_mode(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Set boost mode for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with duration and optional temperature
            
        Returns:
            JSON response
        """
        duration = data.get("duration", 60)
        temp = data.get("temperature")
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.set_boost_mode(duration, temp)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({
                "success": True,
                "boost_active": True,
                "duration": duration,
                "temperature": area.boost_temp
            })
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def cancel_boost(
        self, request: web.Request, area_id: str
    ) -> web.Response:
        """Cancel boost mode for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.cancel_boost_mode()
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "boost_active": False})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def set_frost_protection(
        self, request: web.Request, data: dict
    ) -> web.Response:
        """Set global frost protection settings.
        
        Args:
            request: Request object
            data: Request data with enabled and temperature
            
        Returns:
            JSON response
        """
        enabled = data.get("enabled")
        temp = data.get("temperature")
        
        try:
            if enabled is not None:
                self.area_manager.frost_protection_enabled = enabled
            if temp is not None:
                self.area_manager.frost_protection_temp = temp
            
            await self.area_manager.async_save()
            
            return web.json_response({
                "success": True,
                "enabled": self.area_manager.frost_protection_enabled,
                "temperature": self.area_manager.frost_protection_temp
            })
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def add_window_sensor(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add window sensor to an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with configuration
            
        Returns:
            JSON response
        """
        entity_id = data.get("entity_id")
        if not entity_id:
            return web.json_response(
                {"error": "entity_id required"}, status=400
            )
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            # Extract configuration parameters
            action_when_open = data.get("action_when_open", "reduce_temperature")
            temp_drop = data.get("temp_drop")
            
            area.add_window_sensor(entity_id, action_when_open, temp_drop)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "entity_id": entity_id})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def remove_window_sensor(
        self, request: web.Request, area_id: str, entity_id: str
    ) -> web.Response:
        """Remove window sensor from an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            entity_id: Entity ID to remove
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.remove_window_sensor(entity_id)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def add_presence_sensor(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add presence sensor to an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with configuration
            
        Returns:
            JSON response
        """
        entity_id = data.get("entity_id")
        if not entity_id:
            return web.json_response(
                {"error": "entity_id required"}, status=400
            )
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            # Extract configuration parameters
            action_when_away = data.get("action_when_away", "reduce_temperature")
            action_when_home = data.get("action_when_home", "increase_temperature")
            temp_drop_when_away = data.get("temp_drop_when_away")
            temp_boost_when_home = data.get("temp_boost_when_home")
            
            area.add_presence_sensor(
                entity_id, 
                action_when_away, 
                action_when_home,
                temp_drop_when_away,
                temp_boost_when_home
            )
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "entity_id": entity_id})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def remove_presence_sensor(
        self, request: web.Request, area_id: str, entity_id: str
    ) -> web.Response:
        """Remove presence sensor from an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            entity_id: Entity ID to remove
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.remove_presence_sensor(entity_id)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=404
            )

    async def get_history_config(self, request: web.Request) -> web.Response:
        """Get history configuration.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with history settings
        """
        from .const import DOMAIN, HISTORY_RECORD_INTERVAL_SECONDS
        
        history_tracker = self.hass.data.get(DOMAIN, {}).get("history")
        if not history_tracker:
            return web.json_response(
                {"error": "History not available"}, status=503
            )
        
        return web.json_response({
            "retention_days": history_tracker.get_retention_days(),
            "record_interval_seconds": HISTORY_RECORD_INTERVAL_SECONDS,
            "record_interval_minutes": HISTORY_RECORD_INTERVAL_SECONDS / 60
        })
    
    async def set_history_config(self, request: web.Request, data: dict) -> web.Response:
        """Set history configuration.
        
        Args:
            request: Request object
            data: Configuration data
            
        Returns:
            JSON response
        """
        from .const import DOMAIN
        
        retention_days = data.get("retention_days")
        if not retention_days:
            return web.json_response(
                {"error": "retention_days required"}, status=400
            )
        
        try:
            history_tracker = self.hass.data.get(DOMAIN, {}).get("history")
            if not history_tracker:
                return web.json_response(
                    {"error": "History not available"}, status=503
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

    async def set_hvac_mode(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Set HVAC mode for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with hvac_mode
            
        Returns:
            JSON response
        """
        hvac_mode = data.get("hvac_mode")
        if not hvac_mode:
            return web.json_response(
                {"error": "hvac_mode required"}, status=400
            )
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                raise ValueError(f"Area {area_id} not found")
            
            area.hvac_mode = hvac_mode
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "hvac_mode": hvac_mode})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )


class SmartHeatingUIView(HomeAssistantView):
    """UI view for Smart Heating (no auth required for serving static HTML)."""

    url = "/smart_heating_ui"
    name = "smart_heating:ui"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the UI view.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Serve the UI.
        
        Args:
            request: Request object
            
        Returns:
            HTML response with React app
        """
        import os
        
        # Path to the built frontend
        frontend_path = self.hass.config.path("custom_components/smart_heating/frontend/dist")
        index_path = os.path.join(frontend_path, "index.html")
        
        try:
            async with aiofiles.open(index_path, "r", encoding="utf-8") as f:
                html_content = await f.read()
            
            # Fix asset paths to be relative to our endpoint
            html_content = html_content.replace('src="/', 'src="/smart_heating_static/')
            html_content = html_content.replace('href="/', 'href="/smart_heating_static/')
            
            return web.Response(
                text=html_content,
                content_type="text/html",
                charset="utf-8"
            )
        except FileNotFoundError:
            _LOGGER.error("Frontend build not found at %s", frontend_path)
            return web.Response(
                text="<h1>Frontend not built</h1><p>Run: cd frontend && npm run build</p>",
                content_type="text/html",
                status=500
            )


class SmartHeatingStaticView(HomeAssistantView):
    """Serve static files for Smart Heating UI."""

    url = "/smart_heating_static/{filename:.+}"
    name = "smart_heating:static"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the static view.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    async def get(self, request: web.Request, filename: str) -> web.Response:
        """Serve static files.
        
        Args:
            request: Request object
            filename: File to serve
            
        Returns:
            File response
        """
        import os
        import mimetypes
        
        # Path to the built frontend
        frontend_path = self.hass.config.path("custom_components/smart_heating/frontend/dist")
        file_path = os.path.join(frontend_path, filename)
        
        # Security check - ensure file is within frontend directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(frontend_path)):
            return web.Response(text="Forbidden", status=403)
        
        try:
            # Determine content type
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream"
            
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            
            return web.Response(
                body=content,
                content_type=content_type
            )
        except FileNotFoundError:
            return web.Response(text="Not Found", status=404)


async def setup_api(hass: HomeAssistant, area_manager: AreaManager) -> None:
    """Set up the API.
    
    Args:
        hass: Home Assistant instance
        area_manager: Zone manager instance
    """
    # Register API view
    api_view = SmartHeatingAPIView(hass, area_manager)
    hass.http.register_view(api_view)
    
    # Register UI view (no auth required for serving HTML)
    ui_view = SmartHeatingUIView(hass)
    hass.http.register_view(ui_view)
    
    # Register static files view
    static_view = SmartHeatingStaticView(hass)
    hass.http.register_view(static_view)
    
    _LOGGER.info("Smart Heating API, UI, and static files registered")
