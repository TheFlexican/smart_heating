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
from .area_manager import AreaManager
from .models import Area, Schedule

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
            elif endpoint == "devices/refresh":
                return await self.refresh_devices(request)
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
            elif endpoint.startswith("areas/") and "/logs" in endpoint:
                area_id = endpoint.split("/")[1]
                return await self.get_area_logs(request, area_id)
            elif endpoint == "global_presets":
                return await self.get_global_presets(request)
            elif endpoint == "global_presence":
                return await self.get_global_presence(request)
            elif endpoint == "hysteresis":
                return await self.get_hysteresis(request)
            elif endpoint == "vacation_mode":
                return await self.get_vacation_mode(request)
            elif endpoint == "safety_sensor":
                return await self.get_safety_sensor(request)
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
            elif endpoint.startswith("areas/") and endpoint.endswith("/switch_shutdown"):
                area_id = endpoint.split("/")[1]
                return await self.set_switch_shutdown(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/hysteresis"):
                area_id = endpoint.split("/")[1]
                return await self.set_area_hysteresis(request, area_id, data)
            elif endpoint == "frost_protection":
                return await self.set_frost_protection(request, data)
            elif endpoint == "history/config":
                return await self.set_history_config(request, data)
            elif endpoint == "global_presets":
                return await self.set_global_presets(request, data)
            elif endpoint == "global_presence":
                return await self.set_global_presence(request, data)
            elif endpoint == "hysteresis":
                return await self.set_hysteresis_value(request, data)
            elif endpoint == "vacation_mode":
                return await self.enable_vacation_mode(request, data)
            elif endpoint == "safety_sensor":
                return await self.set_safety_sensor(request, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/preset_config"):
                area_id = endpoint.split("/")[1]
                return await self.set_area_preset_config(request, area_id, data)
            elif endpoint.startswith("areas/") and endpoint.endswith("/manual_override"):
                area_id = endpoint.split("/")[1]
                return await self.set_manual_override(request, area_id, data)
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
            if endpoint == "vacation_mode":
                return await self.disable_vacation_mode(request)
            elif endpoint == "safety_sensor":
                return await self.remove_safety_sensor(request)
            elif endpoint.startswith("areas/") and "/devices/" in endpoint:
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
        from .utils import build_area_response, build_device_info, get_coordinator_devices
        
        # Get Home Assistant's area registry
        area_registry = ar.async_get(self.hass)
        
        areas_data = []
        for area in area_registry.areas.values():
            area_id = area.id
            area_name = area.name
            
            # Check if we have stored data for this area
            stored_area = self.area_manager.get_area(area_id)
            
            if stored_area:
                # Build devices list with coordinator data
                devices_list = []
                coordinator_devices = get_coordinator_devices(self.hass, area_id)
                
                for dev_id, dev_data in stored_area.devices.items():
                    state = self.hass.states.get(dev_id)
                    coord_device = coordinator_devices.get(dev_id)
                    devices_list.append(build_device_info(dev_id, dev_data, state, coord_device))
                
                # Build area response using utility
                area_response = build_area_response(stored_area, devices_list)
                # Override name with HA area name
                area_response["name"] = area_name
                areas_data.append(area_response)
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
                    "manual_override": False,
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
        from .utils import build_area_response, build_device_info
        
        area = self.area_manager.get_area(area_id)
        
        if area is None:
            return web.json_response(
                {"error": f"Zone {area_id} not found"}, status=404
            )
        
        # Build devices list
        devices_list = []
        for dev_id, dev_data in area.devices.items():
            state = self.hass.states.get(dev_id)
            devices_list.append(build_device_info(dev_id, dev_data, state))
        
        # Build area response using utility
        area_data = build_area_response(area, devices_list)
        
        return web.json_response(area_data)

    async def get_devices(self, request: web.Request) -> web.Response:
        """Get available devices from Home Assistant.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with available devices
        """
        from .utils import DeviceRegistry, build_device_dict
        
        devices = []
        device_reg = DeviceRegistry(self.hass)
        entity_registry = er.async_get(self.hass)
        
        _LOGGER.warning("=== SMART HEATING: Starting device discovery ===")
        
        # Build list of hidden areas for filtering
        hidden_areas = [
            {"id": area_id, "name": area.name}
            for area_id, area in self.area_manager.get_all_areas().items()
            if area.hidden
        ]
        
        for entity in entity_registry.entities.values():
            # Skip Smart Heating's own climate entities (zone thermostats)
            if entity.entity_id.startswith("climate.zone_"):
                continue
            
            # Get entity state for additional info
            state = self.hass.states.get(entity.entity_id)
            if not state:
                continue
            
            # Get device type using helper
            device_info = device_reg.get_device_type(entity, state)
            if not device_info:
                continue
            
            device_type, subtype = device_info
            
            # Check if device is already assigned to areas
            assigned_areas = []
            for area_id, area in self.area_manager.get_all_areas().items():
                if entity.entity_id in area.devices:
                    assigned_areas.append(area_id)
                    # If assigned to hidden area, skip it
                    if area.hidden:
                        _LOGGER.debug("Skipping device %s - assigned to hidden area %s", entity.entity_id, area.name)
                        break
            else:
                # Not assigned to hidden area via assignment, check other criteria
                ha_area = device_reg.get_ha_area(entity)
                ha_area_name = ha_area[1] if ha_area else None
                friendly_name = state.attributes.get("friendly_name", "")
                
                # Check if should filter based on hidden area names
                if device_reg.should_filter_device(entity.entity_id, friendly_name, ha_area_name, hidden_areas):
                    continue
                
                # Device passed all filters, add it
                _LOGGER.warning(
                    "DISCOVERED: %s (%s) - type: %s, HA area: %s",
                    friendly_name, entity.entity_id, device_type, ha_area_name or "none"
                )
                
                devices.append(build_device_dict(entity, state, device_type, subtype, ha_area, assigned_areas))
        
        _LOGGER.warning("=== SMART HEATING: Discovery complete - found %d devices ===", len(devices))
        return web.json_response({"devices": devices})

    async def refresh_devices(self, request: web.Request) -> web.Response:
        """Refresh all devices from Home Assistant and update area assignments.
        
        This will re-discover all MQTT devices and overwrite existing device
        configurations with current Home Assistant settings.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with refreshed device count
        """
        _LOGGER.info("Refreshing devices from Home Assistant")
        
        try:
            # Get all MQTT entities from Home Assistant
            entity_registry = er.async_get(self.hass)
            device_registry = dr.async_get(self.hass)
            area_registry = ar.async_get(self.hass)
            
            updated_count = 0
            added_count = 0
            
            # Find entities that are from MQTT and could be heating-related
            for entity in entity_registry.entities.values():
                # Check if entity is from MQTT integration
                if entity.platform == "mqtt":
                    # Get entity state for additional info
                    state = self.hass.states.get(entity.entity_id)
                    if not state:
                        continue
                    
                    # Determine device type based on entity domain
                    device_type = None
                    device_class = state.attributes.get("device_class")
                    
                    if entity.domain == "climate":
                        device_type = "thermostat"
                    elif entity.domain == "sensor":
                        if device_class == "temperature":
                            device_type = "temperature_sensor"
                        else:
                            unit = state.attributes.get("unit_of_measurement", "")
                            if "°C" in unit or "°F" in unit or "temperature" in entity.entity_id.lower():
                                device_type = "temperature_sensor"
                            else:
                                continue
                    elif entity.domain == "switch":
                        if any(keyword in entity.entity_id.lower() 
                               for keyword in ["thermostat", "heater", "radiator", "heating", "pump", "floor", "relay"]):
                            device_type = "switch"
                        else:
                            continue
                    elif entity.domain == "number":
                        if "valve" in entity.entity_id.lower() or device_class == "valve":
                            device_type = "valve"
                        else:
                            continue
                    else:
                        continue
                    
                    if not device_type:
                        continue
                    
                    # Get HA area assignment
                    ha_area_id = None
                    ha_area_name = None
                    if entity.device_id:
                        device_entry = device_registry.async_get(entity.device_id)
                        if device_entry and device_entry.area_id:
                            area_entry = area_registry.async_get_area(device_entry.area_id)
                            if area_entry:
                                ha_area_id = area_entry.id
                                ha_area_name = area_entry.name
                    
                    # Update device in all areas that have it assigned
                    device_updated = False
                    for area_id, area in self.area_manager.get_all_areas().items():
                        if entity.entity_id in area.devices:
                            # Update the device configuration
                            area.devices[entity.entity_id] = {
                                "type": device_type,
                                "mqtt_topic": None  # Will be populated by climate_controller if needed
                            }
                            device_updated = True
                            updated_count += 1
                            _LOGGER.info(
                                "Updated device %s in area %s (type: %s, HA area: %s)",
                                entity.entity_id, area_id, device_type, ha_area_name or "none"
                            )
                    
                    if not device_updated:
                        # Device exists in HA but not assigned to any Smart Heating area
                        added_count += 1
            
            # Save updated configuration
            await self.area_manager.async_save()
            
            _LOGGER.info(
                "Device refresh complete: %d updated, %d available for assignment",
                updated_count, added_count
            )
            
            return web.json_response({
                "success": True,
                "updated": updated_count,
                "available": added_count,
                "message": f"Refreshed {updated_count} devices, {added_count} available for assignment"
            })
            
        except Exception as err:
            _LOGGER.error("Error refreshing devices: %s", err)
            return web.json_response(
                {"error": str(err)}, status=500
            )

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
            "safety_sensors": self.area_manager.get_safety_sensors(),
            "safety_alert_active": self.area_manager.is_safety_alert_active(),
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
                    area.area_manager = self.area_manager
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
        from .utils import validate_temperature, validate_area_id
        
        # Validate area_id
        is_valid, error_msg = validate_area_id(area_id)
        if not is_valid:
            return web.json_response({"error": error_msg}, status=400)
        
        # Validate temperature
        temperature = data.get("temperature")
        is_valid, error_msg = validate_temperature(temperature)
        if not is_valid:
            return web.json_response({"error": error_msg}, status=400)
        
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )
            
            old_temp = area.target_temperature
            old_effective = area.get_effective_target_temperature()
            preset_context = f", preset={area.preset_mode}" if area.preset_mode != "none" else ""
            
            _LOGGER.warning(
                "🌡️ API: SET TEMPERATURE for %s: %.1f°C → %.1f°C%s | Effective: %.1f°C → ?",
                area.name, old_temp, temperature, preset_context, old_effective
            )
            
            self.area_manager.set_area_target_temperature(area_id, temperature)
            
            # Clear manual override mode when user controls temperature via app
            if area and hasattr(area, 'manual_override') and area.manual_override:
                _LOGGER.warning("🔓 Clearing manual override for %s - app now in control", area.name)
                area.manual_override = False
            
            new_effective = area.get_effective_target_temperature()
            _LOGGER.warning(
                "✓ Temperature set: %s now %.1f°C (effective: %.1f°C)",
                area.name, temperature, new_effective
            )
            
            await self.area_manager.async_save()
            
            # Trigger immediate climate control to update devices
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
                _LOGGER.info("Triggered immediate climate control after temperature change")
            
            # Refresh coordinator to notify websocket listeners
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
            
            # Clear safety alert when manually re-enabling areas
            if self.area_manager.is_safety_alert_active():
                self.area_manager.set_safety_alert_active(False)
                _LOGGER.info("Safety alert cleared - area '%s' manually re-enabled", area_id)
            
            # Trigger immediate climate control
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                from .models import Area
                
                # Create area with default settings
                area = Area(
                    area_id=area_id,
                    name=ha_area.name,
                    target_temperature=20.0,
                    enabled=True
                )
                area.area_manager = self.area_manager
                self.area_manager.areas[area_id] = area
            
            area.hidden = True
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                from .models import Area
                
                # Create area with default settings
                area = Area(
                    area_id=area_id,
                    name=ha_area.name,
                    target_temperature=20.0,
                    enabled=True
                )
                area.area_manager = self.area_manager
                self.area_manager.areas[area_id] = area
            
            area.hidden = False
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except Exception as err:
            return web.json_response(
                {"error": str(err)}, status=500
            )
    
    async def set_switch_shutdown(self, request: web.Request, area_id: str, data: dict) -> web.Response:
        """Set whether switches/pumps should shutdown when area is not heating.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: {"shutdown": true/false}
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )
            
            shutdown = data.get("shutdown", True)
            area.shutdown_switches_when_idle = shutdown
            await self.area_manager.async_save()
            
            _LOGGER.info(
                "Area %s: shutdown_switches_when_idle set to %s",
                area_id, shutdown
            )
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except Exception as err:
            _LOGGER.error("Error setting switch shutdown for area %s: %s", area_id, err)
            return web.json_response(
                {"error": str(err)}, status=500
            )
    
    async def set_area_hysteresis(self, request: web.Request, area_id: str, data: dict) -> web.Response:
        """Set area-specific hysteresis or use global setting.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: {"use_global": true/false, "hysteresis": float (optional)}
            
        Returns:
            JSON response
        """
        try:
            area = self.area_manager.get_area(area_id)
            if not area:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )
            
            use_global = data.get("use_global", False)
            
            if use_global:
                # Use global hysteresis setting
                area.hysteresis_override = None
                _LOGGER.info("Area %s: Setting hysteresis_override to None (global)", area_id)
            else:
                # Use area-specific hysteresis
                hysteresis = data.get("hysteresis")
                if hysteresis is None:
                    return web.json_response(
                        {"error": "hysteresis value required when use_global is false"}, 
                        status=400
                    )
                
                # Validate range
                if hysteresis < 0.1 or hysteresis > 2.0:
                    return web.json_response(
                        {"error": "Hysteresis must be between 0.1 and 2.0°C"}, 
                        status=400
                    )
                
                area.hysteresis_override = float(hysteresis)
                _LOGGER.info(
                    "Area %s: Setting hysteresis_override to %.1f°C",
                    area_id, hysteresis
                )
            
            _LOGGER.info("Area %s: hysteresis_override value before save: %s", area_id, area.hysteresis_override)
            await self.area_manager.async_save()
            _LOGGER.info("Area %s: Save completed, verifying value: %s", area_id, area.hysteresis_override)
            
            # Update climate controller if it exists
            if hasattr(area, 'climate_controller') and area.climate_controller:
                # Climate controller will use area.hysteresis_override on next update
                pass
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True})
        except Exception as err:
            _LOGGER.error("Error setting hysteresis for area %s: %s", area_id, err)
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

    async def get_global_presets(self, request: web.Request) -> web.Response:
        """Get global preset temperatures.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with global preset temperatures
        """
        return web.json_response({
            "away_temp": self.area_manager.global_away_temp,
            "eco_temp": self.area_manager.global_eco_temp,
            "comfort_temp": self.area_manager.global_comfort_temp,
            "home_temp": self.area_manager.global_home_temp,
            "sleep_temp": self.area_manager.global_sleep_temp,
            "activity_temp": self.area_manager.global_activity_temp,
        })

    async def set_global_presets(self, request: web.Request, data: dict) -> web.Response:
        """Set global preset temperatures.
        
        Args:
            request: Request object
            data: Dictionary with preset temperatures to update
            
        Returns:
            JSON response
        """
        # Log what's changing
        changes = {k: v for k, v in data.items() if k.endswith("_temp")}
        _LOGGER.warning("🌍 API: SET GLOBAL PRESETS: %s", changes)
        
        # Update global preset temperatures
        if "away_temp" in data:
            old = self.area_manager.global_away_temp
            self.area_manager.global_away_temp = float(data["away_temp"])
            _LOGGER.warning("  Global Away: %.1f°C → %.1f°C", old, self.area_manager.global_away_temp)
        if "eco_temp" in data:
            old = self.area_manager.global_eco_temp
            self.area_manager.global_eco_temp = float(data["eco_temp"])
            _LOGGER.warning("  Global Eco: %.1f°C → %.1f°C", old, self.area_manager.global_eco_temp)
        if "comfort_temp" in data:
            old = self.area_manager.global_comfort_temp
            self.area_manager.global_comfort_temp = float(data["comfort_temp"])
            _LOGGER.warning("  Global Comfort: %.1f°C → %.1f°C", old, self.area_manager.global_comfort_temp)
        if "home_temp" in data:
            old = self.area_manager.global_home_temp
            self.area_manager.global_home_temp = float(data["home_temp"])
            _LOGGER.warning("  Global Home: %.1f°C → %.1f°C", old, self.area_manager.global_home_temp)
        if "sleep_temp" in data:
            old = self.area_manager.global_sleep_temp
            self.area_manager.global_sleep_temp = float(data["sleep_temp"])
            _LOGGER.warning("  Global Sleep: %.1f°C → %.1f°C", old, self.area_manager.global_sleep_temp)
        if "activity_temp" in data:
            old = self.area_manager.global_activity_temp
            self.area_manager.global_activity_temp = float(data["activity_temp"])
            _LOGGER.warning("  Global Activity: %.1f°C → %.1f°C", old, self.area_manager.global_activity_temp)
        
        # Save to storage
        await self.area_manager.async_save()
        
        _LOGGER.warning("✓ Global presets saved")
        
        return web.json_response({"success": True})

    async def get_hysteresis(self, request: web.Request) -> web.Response:
        """Get global hysteresis value.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with hysteresis value
        """
        return web.json_response({
            "hysteresis": self.area_manager.hysteresis
        })

    async def set_hysteresis_value(self, request: web.Request, data: dict) -> web.Response:
        """Set global hysteresis value.
        
        Args:
            request: Request object
            data: Dictionary with hysteresis value
            
        Returns:
            JSON response
        """
        _LOGGER.info("🌡️ API: SET HYSTERESIS: %s", data)
        
        if "hysteresis" in data:
            hysteresis = float(data["hysteresis"])
            # Validate range
            if hysteresis < 0.1 or hysteresis > 2.0:
                return web.json_response(
                    {"error": "Hysteresis must be between 0.1 and 2.0°C"}, 
                    status=400
                )
            
            # Update area manager
            self.area_manager.hysteresis = hysteresis
            await self.area_manager.async_save()
            
            # Update all climate controllers
            for area in self.area_manager.areas.values():
                if hasattr(area, 'climate_controller') and area.climate_controller:
                    area.climate_controller._hysteresis = hysteresis
            
            # Request coordinator update
            await self.coordinator.async_request_refresh()
            
            _LOGGER.info("✅ Hysteresis updated to %.1f°C", hysteresis)
            return web.json_response({"success": True})
        
        return web.json_response(
            {"error": "Missing hysteresis value"}, 
            status=400
        )

    async def get_global_presence(self, request: web.Request) -> web.Response:
        """Get global presence sensors.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with global presence sensors
        """
        return web.json_response({
            "sensors": self.area_manager.global_presence_sensors
        })

    async def set_global_presence(self, request: web.Request, data: dict) -> web.Response:
        """Set global presence sensors.
        
        Args:
            request: Request object
            data: Dictionary with sensors list
            
        Returns:
            JSON response
        """
        _LOGGER.warning("🌍 API: SET GLOBAL PRESENCE: %s", data)
        
        if "sensors" in data:
            self.area_manager.global_presence_sensors = data["sensors"]
            _LOGGER.warning("  Global presence sensors updated: %d sensors", len(self.area_manager.global_presence_sensors))
        
        # Save to storage
        await self.area_manager.async_save()
        
        _LOGGER.warning("✓ Global presence saved")
        
        return web.json_response({"success": True})

    async def get_vacation_mode(self, request: web.Request) -> web.Response:
        """Get vacation mode status and configuration.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with vacation mode data
        """
        vacation_manager = self.hass.data[DOMAIN].get("vacation_manager")
        if not vacation_manager:
            return web.json_response(
                {"error": "Vacation manager not initialized"}, status=500
            )
        
        return web.json_response(vacation_manager.get_data())

    async def enable_vacation_mode(
        self, request: web.Request, data: dict
    ) -> web.Response:
        """Enable vacation mode.
        
        Args:
            request: Request object
            data: Dictionary with vacation mode configuration
            
        Returns:
            JSON response with updated vacation mode data
        """
        vacation_manager = self.hass.data[DOMAIN].get("vacation_manager")
        if not vacation_manager:
            return web.json_response(
                {"error": "Vacation manager not initialized"}, status=500
            )
        
        try:
            result = await vacation_manager.async_enable(
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                preset_mode=data.get("preset_mode", "away"),
                frost_protection_override=data.get("frost_protection_override", True),
                min_temperature=data.get("min_temperature", 10.0),
                auto_disable=data.get("auto_disable", True),
                person_entities=data.get("person_entities", [])
            )
            
            # Broadcast vacation mode change via WebSocket
            self.hass.bus.async_fire(
                f"{DOMAIN}_vacation_mode_changed",
                {"enabled": True, "data": result}
            )
            
            _LOGGER.info("Vacation mode enabled via API")
            return web.json_response(result)
        except ValueError as err:
            return web.json_response({"error": str(err)}, status=400)

    async def disable_vacation_mode(self, request: web.Request) -> web.Response:
        """Disable vacation mode.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with updated vacation mode data
        """
        vacation_manager = self.hass.data[DOMAIN].get("vacation_manager")
        if not vacation_manager:
            return web.json_response(
                {"error": "Vacation manager not initialized"}, status=500
            )
        
        result = await vacation_manager.async_disable()
        
        # Broadcast vacation mode change via WebSocket
        self.hass.bus.async_fire(
            f"{DOMAIN}_vacation_mode_changed",
            {"enabled": False, "data": result}
        )
        
        _LOGGER.info("Vacation mode disabled via API")
        return web.json_response(result)

    async def get_safety_sensor(self, request: web.Request) -> web.Response:
        """Get all safety sensor configurations.
        
        Args:
            request: Request object
            
        Returns:
            JSON response with list of safety sensors
        """
        sensors = self.area_manager.get_safety_sensors()
        
        return web.json_response({
            "sensors": sensors,
            "alert_active": self.area_manager.is_safety_alert_active(),
        })

    async def set_safety_sensor(
        self, request: web.Request, data: dict
    ) -> web.Response:
        """Add or update a safety sensor.
        
        Args:
            request: Request object
            data: Dictionary with sensor configuration
            
        Returns:
            JSON response with updated configuration
        """
        sensor_id = data.get("sensor_id")
        attribute = data.get("attribute", "smoke")
        alert_value = data.get("alert_value", True)
        enabled = data.get("enabled", True)
        
        if not sensor_id:
            return web.json_response(
                {"error": "sensor_id is required"}, status=400
            )
        
        # Add or update safety sensor
        self.area_manager.add_safety_sensor(sensor_id, attribute, alert_value, enabled)
        await self.area_manager.async_save()
        
        # Reconfigure safety monitor
        safety_monitor = self.hass.data[DOMAIN].get("safety_monitor")
        if safety_monitor:
            await safety_monitor.async_reconfigure()
        
        # Broadcast configuration change via WebSocket
        self.hass.bus.async_fire(
            f"{DOMAIN}_safety_sensor_changed",
            {
                "sensor_id": sensor_id,
                "attribute": attribute,
                "alert_value": alert_value,
                "enabled": enabled,
            }
        )
        
        _LOGGER.info(
            "Safety sensor configured via API: %s (attribute: %s, enabled: %s)",
            sensor_id, attribute, enabled
        )
        
        return web.json_response({
            "sensor_id": sensor_id,
            "attribute": attribute,
            "alert_value": alert_value,
            "enabled": enabled,
        })

    async def remove_safety_sensor(self, request: web.Request) -> web.Response:
        """Remove a safety sensor configuration.
        
        Args:
            request: Request object (sensor_id in query params or body)
            
        Returns:
            JSON response
        """
        # Get sensor_id from query params or body
        sensor_id = request.query.get("sensor_id")
        if not sensor_id:
            try:
                data = await request.json()
                sensor_id = data.get("sensor_id")
            except:
                pass
        
        if not sensor_id:
            return web.json_response(
                {"error": "sensor_id is required"}, status=400
            )
        
        self.area_manager.remove_safety_sensor(sensor_id)
        await self.area_manager.async_save()
        
        # Reconfigure safety monitor
        safety_monitor = self.hass.data[DOMAIN].get("safety_monitor")
        if safety_monitor:
            await safety_monitor.async_reconfigure()
        
        # Broadcast configuration change via WebSocket
        self.hass.bus.async_fire(
            f"{DOMAIN}_safety_sensor_changed",
            {"sensor_id": None, "enabled": False}
        )
        
        _LOGGER.info("Safety sensor removed via API")
        return web.json_response({"success": True})

    async def set_area_preset_config(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Set per-area preset configuration (use global vs custom temperatures).
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Dictionary with use_global_* flags
            
        Returns:
            JSON response
        """
        area = self.area_manager.get_area(area_id)
        if not area:
            return web.json_response(
                {"error": f"Area {area_id} not found"}, status=404
            )
        
        changes = {k: v for k, v in data.items() if k.startswith("use_global_")}
        _LOGGER.warning("⚙️  API: SET PRESET CONFIG for %s: %s", area.name, changes)
        
        # Update use_global_* flags
        if "use_global_away" in data:
            area.use_global_away = bool(data["use_global_away"])
        if "use_global_eco" in data:
            area.use_global_eco = bool(data["use_global_eco"])
        if "use_global_comfort" in data:
            area.use_global_comfort = bool(data["use_global_comfort"])
        if "use_global_home" in data:
            area.use_global_home = bool(data["use_global_home"])
        if "use_global_sleep" in data:
            area.use_global_sleep = bool(data["use_global_sleep"])
        if "use_global_activity" in data:
            area.use_global_activity = bool(data["use_global_activity"])
        if "use_global_presence" in data:
            area.use_global_presence = bool(data["use_global_presence"])
        
        # Save to storage
        await self.area_manager.async_save()
        
        _LOGGER.warning("✓ Preset config saved for %s", area.name)
        
        # Refresh coordinator to update frontend
        entry_ids = [
            key for key in self.hass.data[DOMAIN].keys()
            if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
        ]
        if entry_ids:
            coordinator = self.hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()
        
        return web.json_response({"success": True})

    async def set_manual_override(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Toggle manual override mode for an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Dictionary with 'enabled' boolean
            
        Returns:
            JSON response
        """
        area = self.area_manager.get_area(area_id)
        if not area:
            return web.json_response(
                {"error": f"Area {area_id} not found"}, status=404
            )
        
        enabled = data.get("enabled")
        if enabled is None:
            return web.json_response(
                {"error": "enabled field is required"}, status=400
            )
        
        old_state = area.manual_override
        area.manual_override = bool(enabled)
        
        _LOGGER.warning(
            "🎛️ API: MANUAL OVERRIDE for %s: %s → %s",
            area.name,
            "ON" if old_state else "OFF",
            "ON" if area.manual_override else "OFF"
        )
        
        # If turning off manual override and there's an active preset, update target to preset temp
        if not area.manual_override and area.preset_mode and area.preset_mode != "none":
            effective_temp = area.get_effective_target_temperature()
            old_target = area.target_temperature
            # Update the base target temperature to match the preset temperature
            # This ensures the UI shows the correct temperature
            area.target_temperature = effective_temp
            _LOGGER.warning(
                "✓ %s now using preset mode '%s': %.1f°C → %.1f°C",
                area.name, area.preset_mode, old_target, effective_temp
            )
        
        # Save to storage
        await self.area_manager.async_save()
        
        # Trigger climate control to apply changes
        climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
        if climate_controller:
            await climate_controller.async_control_heating()
        
        # Refresh coordinator
        entry_ids = [
            key for key in self.hass.data[DOMAIN].keys()
            if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
        ]
        if entry_ids:
            coordinator = self.hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()
        
        return web.json_response({"success": True})

    async def add_schedule(
        self, request: web.Request, area_id: str, data: dict
    ) -> web.Response:
        """Add schedule to an area.
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Schedule data (day, start_time, end_time, temperature or preset_mode)
            
        Returns:
            JSON response
        """
        import uuid
        from .utils import validate_area_id, validate_temperature
        
        # Validate area_id
        is_valid, error_msg = validate_area_id(area_id)
        if not is_valid:
            return web.json_response({"error": error_msg}, status=400)
        
        schedule_id = data.get("id") or str(uuid.uuid4())
        temperature = data.get("temperature")
        preset_mode = data.get("preset_mode")
        
        # Require either temperature or preset_mode
        if temperature is None and preset_mode is None:
            return web.json_response(
                {"error": "Either temperature or preset_mode is required"}, status=400
            )
        
        # Validate temperature if provided
        if temperature is not None:
            is_valid, error_msg = validate_temperature(temperature)
            if not is_valid:
                return web.json_response({"error": error_msg}, status=400)
        
        try:
            # Ensure area exists in storage
            if self.area_manager.get_area(area_id) is None:
                # Auto-create area entry for this HA area if not exists
                area_registry = ar.async_get(self.hass)
                ha_area = area_registry.async_get_area(area_id)
                if ha_area:
                    # Create internal storage for this HA area
                    from .models import Area
                    area = Area(area_id, ha_area.name)
                    area.area_manager = self.area_manager
                    self.area_manager.areas[area_id] = area
                else:
                    return web.json_response(
                        {"error": f"Area {area_id} not found"}, status=404
                    )
            
            # Create schedule from frontend data
            from .models import Schedule
            
            # Validate required fields - accept either 'time' (legacy) or 'start_time' (new)
            time_str = data.get("time") or data.get("start_time")
            if not time_str:
                return web.json_response(
                    {"error": "Missing required field: time or start_time"}, status=400
                )
            
            schedule = Schedule(
                schedule_id=schedule_id,
                time=time_str,
                temperature=temperature,
                days=data.get("days"),
                enabled=data.get("enabled", True),
                day=data.get("day"),
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                preset_mode=data.get("preset_mode"),
                date=data.get("date"),
            )
            
            area = self.area_manager.get_area(area_id)
            if not area:
                return web.json_response(
                    {"error": f"Area {area_id} not found"}, status=404
                )
            
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
            
            # Clear the schedule cache so the scheduler re-evaluates immediately
            schedule_executor = self.hass.data[DOMAIN].get("schedule_executor")
            if schedule_executor:
                schedule_executor.clear_schedule_cache(area_id)
            
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
            
            old_preset = area.preset_mode
            old_target = area.target_temperature
            old_effective = area.get_effective_target_temperature()
            
            _LOGGER.warning(
                "🎛️  API: SET PRESET MODE for %s: '%s' → '%s' | Current temp: %.1f°C, Effective: %.1f°C",
                area.name, old_preset, preset_mode, old_target, old_effective
            )
            
            area.set_preset_mode(preset_mode)
            
            # Clear manual override mode when user sets preset via app
            if hasattr(area, 'manual_override') and area.manual_override:
                _LOGGER.warning("🔓 Clearing manual override for %s - preset mode now in control", area.name)
                area.manual_override = False
            
            await self.area_manager.async_save()
            
            # Get new effective temperature
            new_effective = area.get_effective_target_temperature()
            
            _LOGGER.warning(
                "✓ Preset applied: %s → '%s' | Effective temp: %.1f°C → %.1f°C (base: %.1f°C)",
                area.name, preset_mode, old_effective, new_effective, old_target
            )
            
            # Trigger immediate climate control to apply new temperature
            climate_controller = self.hass.data.get(DOMAIN, {}).get("climate_controller")
            if climate_controller:
                await climate_controller.async_control_heating()
                _LOGGER.info("Triggered immediate climate control after preset change")
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
        
        Presence sensors control preset mode switching:
        - When away: Switch to "away" preset
        - When home: Switch back to previous preset
        
        Args:
            request: Request object
            area_id: Area identifier
            data: Request data with entity_id
            
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
            
            area.add_presence_sensor(entity_id)
            await self.area_manager.async_save()
            
            # Refresh coordinator
            entry_ids = [
                key for key in self.hass.data[DOMAIN].keys()
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
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
                if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
            ]
            if entry_ids:
                coordinator = self.hass.data[DOMAIN][entry_ids[0]]
                await coordinator.async_request_refresh()
            
            return web.json_response({"success": True, "hvac_mode": hvac_mode})
        except ValueError as err:
            return web.json_response(
                {"error": str(err)}, status=400
            )

    async def get_area_logs(self, request: web.Request, area_id: str) -> web.Response:
        """Get logs for a specific area.
        
        Args:
            request: Request object
            area_id: Area identifier
            
        Returns:
            JSON response with logs
        """
        try:
            # Get optional query parameters
            limit = request.query.get("limit")
            event_type = request.query.get("type")
            
            # Get area logger from hass data
            area_logger = self.hass.data[DOMAIN].get("area_logger")
            if not area_logger:
                return web.json_response({"logs": []})
            
            # Get logs (async)
            logs = await area_logger.async_get_logs(
                area_id=area_id,
                limit=int(limit) if limit else None,
                event_type=event_type
            )
            
            return web.json_response({"logs": logs})
            
        except Exception as err:
            _LOGGER.error("Error getting logs for area %s: %s", area_id, err)
            return web.json_response(
                {"error": str(err)}, status=500
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
