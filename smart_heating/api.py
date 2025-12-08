"""Flask API server for Smart Heating - Refactored to use modular handlers."""
import logging

from aiohttp import web
import aiofiles

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .area_manager import AreaManager
from .api_handlers import (
    # Areas
    handle_get_areas,
    handle_get_area,
    handle_set_temperature,
    handle_enable_area,
    handle_disable_area,
    handle_hide_area,
    handle_unhide_area,
    handle_set_switch_shutdown,
    handle_set_area_hysteresis,
    handle_set_auto_preset,
    handle_set_area_preset_config,
    handle_set_manual_override,
    handle_set_primary_temperature_sensor,
    # Devices
    handle_get_devices,
    handle_refresh_devices,
    handle_add_device,
    handle_remove_device,
    # Schedules
    handle_add_schedule,
    handle_remove_schedule,
    handle_set_preset_mode,
    handle_set_boost_mode,
    handle_cancel_boost,
    # Sensors
    handle_add_window_sensor,
    handle_remove_window_sensor,
    handle_add_presence_sensor,
    handle_remove_presence_sensor,
    handle_get_binary_sensor_entities,
    # Config
    handle_get_config,
    handle_get_global_presets,
    handle_set_global_presets,
    handle_get_hysteresis,
    handle_set_hysteresis_value,
    handle_get_global_presence,
    handle_set_global_presence,
    handle_set_frost_protection,
    handle_get_vacation_mode,
    handle_enable_vacation_mode,
    handle_disable_vacation_mode,
    handle_get_safety_sensor,
    handle_set_safety_sensor,
    handle_remove_safety_sensor,
    handle_set_hvac_mode,
    # History
    handle_get_history,
    handle_get_learning_stats,
    handle_get_history_config,
    handle_set_history_config,
    # Logs
    handle_get_area_logs,
    # System
    handle_get_status,
    handle_get_entity_state,
    handle_call_service,
)

_LOGGER = logging.getLogger(__name__)

# Constants for error messages and endpoints
ERROR_UNKNOWN_ENDPOINT = "Unknown endpoint"
ENDPOINT_PREFIX_AREAS = "areas/"


class SmartHeatingAPIView(HomeAssistantView):
    """API view for Smart Heating - uses modular handlers."""

    url = "/api/smart_heating/{endpoint:.*}"
    name = "api:smart_heating"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager) -> None:
        """Initialize the API view.
        
        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
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
            # System endpoints
            if endpoint == "status":
                return await handle_get_status(self.area_manager)
            elif endpoint == "config":
                return await handle_get_config(self.hass, self.area_manager)
            
            # Area endpoints
            elif endpoint == "areas":
                return await handle_get_areas(self.hass, self.area_manager)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/history" in endpoint:
                area_id = endpoint.split("/")[1]
                return await handle_get_history(self.hass, area_id, request)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/learning" in endpoint:
                area_id = endpoint.split("/")[1]
                return await handle_get_learning_stats(self.hass, area_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/logs" in endpoint:
                area_id = endpoint.split("/")[1]
                return await handle_get_area_logs(self.hass, area_id, request)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS):
                area_id = endpoint.split("/")[1]
                return await handle_get_area(self.hass, self.area_manager, area_id)
            
            # Device endpoints
            elif endpoint == "devices":
                return await handle_get_devices(self.hass, self.area_manager)
            elif endpoint == "devices/refresh":
                return await handle_refresh_devices(self.hass, self.area_manager)
            
            # Sensor endpoints
            elif endpoint == "entities/binary_sensor":
                return await handle_get_binary_sensor_entities(self.hass)
            
            # Entity state endpoint
            elif endpoint.startswith("entity_state/"):
                entity_id = endpoint.replace("entity_state/", "")
                return await handle_get_entity_state(self.hass, entity_id)
            
            # Config endpoints
            elif endpoint == "global_presets":
                return await handle_get_global_presets(self.area_manager)
            elif endpoint == "global_presence":
                return await handle_get_global_presence(self.area_manager)
            elif endpoint == "hysteresis":
                return await handle_get_hysteresis(self.area_manager)
            elif endpoint == "vacation_mode":
                return await handle_get_vacation_mode(self.hass)
            elif endpoint == "safety_sensor":
                return await handle_get_safety_sensor(self.area_manager)
            elif endpoint == "history/config":
                return await handle_get_history_config(self.hass)
            
            else:
                return web.json_response(
                    {"error": ERROR_UNKNOWN_ENDPOINT}, status=404
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
            if endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/enable"):
                area_id = endpoint.split("/")[1]
                return await handle_enable_area(self.hass, self.area_manager, area_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/disable"):
                area_id = endpoint.split("/")[1]
                return await handle_disable_area(self.hass, self.area_manager, area_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/hide"):
                area_id = endpoint.split("/")[1]
                return await handle_hide_area(self.hass, self.area_manager, area_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/unhide"):
                area_id = endpoint.split("/")[1]
                return await handle_unhide_area(self.hass, self.area_manager, area_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/cancel_boost"):
                area_id = endpoint.split("/")[1]
                return await handle_cancel_boost(self.hass, self.area_manager, area_id)
            
            # Parse JSON for endpoints that need it
            data = await request.json()
            _LOGGER.debug("POST data: %s", data)
            
            # Area endpoints with data
            if endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/devices"):
                area_id = endpoint.split("/")[1]
                return await handle_add_device(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/schedules"):
                area_id = endpoint.split("/")[1]
                return await handle_add_schedule(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/temperature"):
                area_id = endpoint.split("/")[1]
                return await handle_set_temperature(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/preset_mode"):
                area_id = endpoint.split("/")[1]
                return await handle_set_preset_mode(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/boost"):
                area_id = endpoint.split("/")[1]
                return await handle_set_boost_mode(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/window_sensors"):
                area_id = endpoint.split("/")[1]
                return await handle_add_window_sensor(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/presence_sensors"):
                area_id = endpoint.split("/")[1]
                return await handle_add_presence_sensor(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/hvac_mode"):
                area_id = endpoint.split("/")[1]
                return await handle_set_hvac_mode(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/switch_shutdown"):
                area_id = endpoint.split("/")[1]
                return await handle_set_switch_shutdown(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/hysteresis"):
                area_id = endpoint.split("/")[1]
                return await handle_set_area_hysteresis(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/auto_preset"):
                area_id = endpoint.split("/")[1]
                return await handle_set_auto_preset(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/preset_config"):
                area_id = endpoint.split("/")[1]
                return await handle_set_area_preset_config(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/manual_override"):
                area_id = endpoint.split("/")[1]
                return await handle_set_manual_override(self.hass, self.area_manager, area_id, data)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and endpoint.endswith("/primary_temp_sensor"):
                area_id = endpoint.split("/")[1]
                return await handle_set_primary_temperature_sensor(self.hass, self.area_manager, area_id, data)
            
            # Global config endpoints
            elif endpoint == "frost_protection":
                return await handle_set_frost_protection(self.area_manager, data)
            elif endpoint == "history/config":
                return await handle_set_history_config(self.hass, data)
            elif endpoint == "global_presets":
                return await handle_set_global_presets(self.area_manager, data)
            elif endpoint == "global_presence":
                return await handle_set_global_presence(self.area_manager, data)
            elif endpoint == "hysteresis":
                # Get coordinator
                entry_ids = [
                    key for key in self.hass.data[DOMAIN].keys()
                    if key not in ["history", "climate_controller", "schedule_executor", "climate_unsub", "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
                ]
                coordinator = self.hass.data[DOMAIN][entry_ids[0]] if entry_ids else None
                return await handle_set_hysteresis_value(self.hass, self.area_manager, coordinator, data)
            elif endpoint == "vacation_mode":
                return await handle_enable_vacation_mode(self.hass, data)
            elif endpoint == "safety_sensor":
                return await handle_set_safety_sensor(self.hass, self.area_manager, data)
            elif endpoint == "call_service":
                return await handle_call_service(self.hass, data)
            else:
                return web.json_response(
                    {"error": ERROR_UNKNOWN_ENDPOINT}, status=404
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
                return await handle_disable_vacation_mode(self.hass)
            elif endpoint == "safety_sensor":
                return await handle_remove_safety_sensor(self.hass, self.area_manager)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/devices/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                device_id = parts[3]
                return await handle_remove_device(self.area_manager, area_id, device_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/schedules/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                schedule_id = parts[3]
                return await handle_remove_schedule(self.hass, self.area_manager, area_id, schedule_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/window_sensors/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await handle_remove_window_sensor(self.hass, self.area_manager, area_id, entity_id)
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/presence_sensors/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await handle_remove_presence_sensor(self.hass, self.area_manager, area_id, entity_id)
            else:
                return web.json_response(
                    {"error": ERROR_UNKNOWN_ENDPOINT}, status=404
                )
        except Exception as err:
            _LOGGER.error("Error handling DELETE %s: %s", endpoint, err)
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
        area_manager: Area manager instance
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
