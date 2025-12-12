"""Flask API server for Smart Heating - Refactored to use modular handlers."""

import logging

import aiofiles
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .api_handlers import (
    handle_add_device,
    handle_add_presence_sensor,
    # Schedules
    handle_add_schedule,
    # Sensors
    handle_add_window_sensor,
    handle_call_service,
    handle_cancel_boost,
    handle_create_user,
    handle_delete_user,
    handle_disable_area,
    handle_disable_vacation_mode,
    handle_enable_area,
    handle_enable_vacation_mode,
    handle_export_config,
    handle_get_active_preferences,
    handle_get_area,
    handle_get_area_efficiency_history,
    # Logs
    handle_get_area_logs,
    # Areas
    handle_get_areas,
    handle_get_binary_sensor_entities,
    handle_get_weather_entities,
    # Config
    handle_get_comparison,
    handle_get_config,
    handle_get_custom_comparison,
    # Devices
    handle_get_devices,
    handle_get_efficiency_report,
    handle_get_entity_state,
    handle_get_global_presence,
    handle_get_global_presets,
    # History
    handle_get_history,
    handle_get_history_config,
    handle_get_history_storage_info,
    handle_get_database_stats,
    handle_migrate_history_storage,
    handle_cleanup_history,
    handle_get_hysteresis,
    handle_get_learning_stats,
    handle_get_presence_state,
    handle_get_safety_sensor,
    # System
    handle_get_status,
    handle_get_user,
    handle_get_users,
    handle_get_vacation_mode,
    handle_hide_area,
    handle_import_config,
    handle_list_backups,
    handle_refresh_devices,
    handle_remove_device,
    handle_remove_presence_sensor,
    handle_remove_safety_sensor,
    handle_remove_schedule,
    handle_remove_window_sensor,
    handle_restore_backup,
    handle_set_area_hysteresis,
    handle_set_area_preset_config,
    handle_set_area_heating_curve,
    handle_set_auto_preset,
    handle_set_heating_type,
    handle_set_boost_mode,
    handle_set_frost_protection,
    handle_set_global_presence,
    handle_set_global_presets,
    handle_set_hide_devices_panel,
    handle_set_history_config,
    handle_set_hvac_mode,
    handle_set_hysteresis_value,
    handle_set_manual_override,
    handle_set_advanced_control_config,
    handle_set_opentherm_gateway,
    handle_set_preset_mode,
    handle_set_primary_temperature_sensor,
    handle_set_safety_sensor,
    handle_set_switch_shutdown,
    handle_set_temperature,
    handle_unhide_area,
    handle_update_user,
    handle_update_user_settings,
    handle_validate_config,
)
from .api_handlers.opentherm import (
    handle_get_opentherm_logs,
    handle_get_opentherm_capabilities,
    handle_discover_opentherm_capabilities,
    handle_clear_opentherm_logs,
    handle_get_opentherm_gateways,
    handle_calibrate_opentherm,
)
from .area_manager import AreaManager
from .const import DOMAIN
from .coordinator import SmartHeatingCoordinator

_LOGGER = logging.getLogger(__name__)

# Constants for error messages and endpoints
ERROR_UNKNOWN_ENDPOINT = "Unknown endpoint"
ENDPOINT_PREFIX_AREAS = "areas/"
_USERS_PATH = "users/"


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

    def _get_coordinator(self) -> SmartHeatingCoordinator | None:
        """Return first SmartHeatingCoordinator instance stored in hass.data for this domain."""
        domain_data = self.hass.data.get(DOMAIN, {})
        for v in domain_data.values():
            if isinstance(v, SmartHeatingCoordinator):
                return v
        return None

    async def _handle_area_endpoints_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle area-related GET endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        if endpoint == "areas":
            return await handle_get_areas(self.hass, self.area_manager)

        if not endpoint.startswith(ENDPOINT_PREFIX_AREAS):
            return None

        area_id = endpoint.split("/")[1]

        if "/history" in endpoint:
            return await handle_get_history(self.hass, area_id, request)
        elif "/learning" in endpoint:
            return await handle_get_learning_stats(self.hass, area_id)
        elif "/logs" in endpoint:
            return await handle_get_area_logs(self.hass, area_id, request)
        elif "/efficiency" in endpoint:
            efficiency_calculator = self.hass.data[DOMAIN]["efficiency_calculator"]
            return await handle_get_area_efficiency_history(
                self.hass, efficiency_calculator, request, area_id
            )
        else:
            return await handle_get_area(self.hass, self.area_manager, area_id)

    async def _handle_config_endpoints_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle configuration GET endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        config_handlers = {
            "config": lambda: handle_get_config(self.hass, self.area_manager),
            "global_presets": lambda: handle_get_global_presets(self.area_manager),
            "global_presence": lambda: handle_get_global_presence(self.area_manager),
            "hysteresis": lambda: handle_get_hysteresis(self.area_manager),
            "vacation_mode": lambda: handle_get_vacation_mode(self.hass),
            "safety_sensor": lambda: handle_get_safety_sensor(self.area_manager),
            "config/advanced_control": lambda: handle_get_config(
                self.hass, self.area_manager
            ),
            "history/config": lambda: handle_get_history_config(self.hass),
            "history/storage/info": lambda: handle_get_history_storage_info(self.hass),
            "history/storage/database/stats": lambda: handle_get_database_stats(
                self.hass
            ),
        }

        handler = config_handlers.get(endpoint)
        return await handler() if handler else None

    async def _handle_user_endpoints_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle user-related GET endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        user_manager = self.hass.data.get(DOMAIN, {}).get("user_manager")
        if not user_manager:
            return None

        if endpoint == "users":
            return await handle_get_users(self.hass, user_manager, request)
        elif endpoint.startswith(_USERS_PATH) and not endpoint.endswith("/"):
            user_id = endpoint.split("/")[1]
            return await handle_get_user(self.hass, user_manager, request, user_id)
        elif endpoint == f"{_USERS_PATH}presence":
            return await handle_get_presence_state(self.hass, user_manager, request)
        elif endpoint == f"{_USERS_PATH}preferences":
            return await handle_get_active_preferences(self.hass, user_manager, request)

        return None

    async def _handle_efficiency_endpoints_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle efficiency GET endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        if not endpoint.startswith("efficiency"):
            return None

        efficiency_calculator = self.hass.data.get(DOMAIN, {}).get(
            "efficiency_calculator"
        )
        if not efficiency_calculator:
            return None

        if endpoint == "efficiency/all_areas":
            return await handle_get_efficiency_report(
                self.hass, self.area_manager, efficiency_calculator, request
            )
        elif endpoint.startswith("efficiency/report/"):
            area_id = endpoint.split("/")[2]
            period = request.query.get("period", "week")
            area_metrics = await efficiency_calculator.calculate_area_efficiency(
                area_id, period
            )
            response_data = {
                "area_id": area_metrics.get("area_id"),
                "period": area_metrics.get("period"),
                "start_date": area_metrics.get("start_time", ""),
                "end_date": area_metrics.get("end_time", ""),
                "metrics": {
                    "energy_score": area_metrics.get("energy_score", 0),
                    "heating_time_percentage": area_metrics.get(
                        "heating_time_percentage", 0
                    ),
                    "heating_cycles": area_metrics.get("heating_cycles", 0),
                    "avg_temp_delta": area_metrics.get("average_temperature_delta", 0),
                },
                "recommendations": area_metrics.get("recommendations", []),
            }
            return web.json_response(response_data)
        elif endpoint.startswith("efficiency/history/"):
            area_id = endpoint.split("/")[2]
            return await handle_get_area_efficiency_history(
                self.hass, efficiency_calculator, request, area_id
            )

        return None

    async def _handle_devices_sensors_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle device and sensor endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        # Device endpoints
        if endpoint == "devices":
            return await handle_get_devices(self.hass, self.area_manager)
        elif endpoint == "devices/refresh":
            return await handle_refresh_devices(self.hass, self.area_manager)

        # Sensor endpoints
        elif endpoint == "entities/binary_sensor":
            return await handle_get_binary_sensor_entities(self.hass)
        elif endpoint == "entities/weather":
            return await handle_get_weather_entities(self.hass)

        # Entity state endpoint
        elif endpoint.startswith("entity_state/"):
            entity_id = endpoint.replace("entity_state/", "")
            return await handle_get_entity_state(self.hass, entity_id)

        return None

    async def _handle_opentherm_metrics_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle OpenTherm and metrics endpoints.

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        # OpenTherm endpoints
        if endpoint == "opentherm/logs":
            return await handle_get_opentherm_logs(self.hass, request)
        elif endpoint == "opentherm/capabilities":
            return await handle_get_opentherm_capabilities(self.hass)
        elif endpoint == "opentherm/gateways":
            return await handle_get_opentherm_gateways(self.hass)
        elif endpoint == "opentherm/calibrate":
            return await handle_calibrate_opentherm(
                self.hass, self.area_manager, self._get_coordinator()
            )

        # Advanced metrics endpoints
        if endpoint == "metrics/advanced":
            advanced_metrics = self.hass.data.get(DOMAIN, {}).get(
                "advanced_metrics_collector"
            )
            if not advanced_metrics:
                return web.json_response(
                    {"error": "Advanced metrics collector not available"}, status=503
                )

            days = int(request.query.get("days", "7"))
            area_id = request.query.get("area_id")

            if days not in [1, 3, 7, 30]:
                return web.json_response(
                    {"error": "days must be 1, 3, 7, or 30"}, status=400
                )

            metrics = await advanced_metrics.async_get_metrics(days, area_id)
            return web.json_response(
                {"success": True, "days": days, "area_id": area_id, "metrics": metrics}
            )

        return None

    async def _handle_other_endpoints_get(
        self, request: web.Request, endpoint: str
    ) -> web.Response | None:
        """Handle miscellaneous GET endpoints (devices, sensors, comparison, opentherm, metrics).

        Args:
            request: Request object
            endpoint: Endpoint path

        Returns:
            Response if handled, None otherwise
        """
        # Devices and sensors
        response = await self._handle_devices_sensors_get(request, endpoint)
        if response:
            return response

        # Config endpoints
        response = await self._handle_config_endpoints_get(request, endpoint)
        if response:
            return response

        # Import/Export endpoints
        if endpoint in ("export", "backups"):
            config_manager = self.hass.data.get(DOMAIN, {}).get("config_manager")
            if not config_manager:
                return None
            if endpoint == "export":
                return await handle_export_config(self.hass, config_manager)
            return await handle_list_backups(self.hass, config_manager)

        # User endpoints
        response = await self._handle_user_endpoints_get(request, endpoint)
        if response:
            return response

        # Efficiency endpoints
        response = await self._handle_efficiency_endpoints_get(request, endpoint)
        if response:
            return response

        # Comparison endpoints
        if endpoint.startswith("comparison"):
            comparison_engine = self.hass.data.get(DOMAIN, {}).get("comparison_engine")
            if not comparison_engine:
                return None

            if endpoint.startswith("comparison/custom"):
                return await handle_get_custom_comparison(
                    self.hass, comparison_engine, request
                )
            return await handle_get_comparison(
                self.hass, self.area_manager, comparison_engine, request
            )

        # OpenTherm and metrics
        response = await self._handle_opentherm_metrics_get(request, endpoint)
        if response:
            return response

        return None

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

            # Area endpoints
            response = await self._handle_area_endpoints_get(request, endpoint)
            if response:
                return response

            # Try all other endpoint handlers
            response = await self._handle_other_endpoints_get(request, endpoint)
            if response:
                return response

            else:
                return web.json_response({"error": ERROR_UNKNOWN_ENDPOINT}, status=404)
        except Exception as err:
            _LOGGER.error("Error handling GET %s: %s", endpoint, err)
            return web.json_response({"error": str(err)}, status=500)

    async def _handle_area_action_post(
        self, endpoint: str, action: str
    ) -> web.Response | None:
        """Handle area action endpoints (no body required).

        Args:
            endpoint: Full endpoint path
            action: Action name (enable, disable, hide, unhide, cancel_boost)

        Returns:
            Response if handled, None otherwise
        """
        if not endpoint.startswith(ENDPOINT_PREFIX_AREAS):
            return None

        if endpoint.endswith(f"/{action}"):
            area_id = endpoint.split("/")[1]
            handlers = {
                "enable": handle_enable_area,
                "disable": handle_disable_area,
                "hide": handle_hide_area,
                "unhide": handle_unhide_area,
                "cancel_boost": handle_cancel_boost,
            }
            handler = handlers.get(action)
            if handler:
                return await handler(self.hass, self.area_manager, area_id)
        return None

    async def _handle_area_data_post(
        self, endpoint: str, data: dict
    ) -> web.Response | None:
        """Handle area endpoints that require data.

        Args:
            endpoint: Full endpoint path
            data: Request body data

        Returns:
            Response if handled, None otherwise
        """
        if not endpoint.startswith(ENDPOINT_PREFIX_AREAS):
            return None

        area_id = endpoint.split("/")[1]

        # Map endpoint suffixes to handlers
        endpoint_handlers = {
            "/devices": lambda: handle_add_device(
                self.hass, self.area_manager, area_id, data
            ),
            "/schedules": lambda: handle_add_schedule(
                self.hass, self.area_manager, area_id, data
            ),
            "/temperature": lambda: handle_set_temperature(
                self.hass, self.area_manager, area_id, data
            ),
            "/preset_mode": lambda: handle_set_preset_mode(
                self.hass, self.area_manager, area_id, data
            ),
            "/boost": lambda: handle_set_boost_mode(
                self.hass, self.area_manager, area_id, data
            ),
            "/window_sensors": lambda: handle_add_window_sensor(
                self.hass, self.area_manager, area_id, data
            ),
            "/presence_sensors": lambda: handle_add_presence_sensor(
                self.hass, self.area_manager, area_id, data
            ),
            "/hvac_mode": lambda: handle_set_hvac_mode(
                self.hass, self.area_manager, area_id, data
            ),
            "/heating_curve": lambda: handle_set_area_heating_curve(
                self.hass, self.area_manager, area_id, data
            ),
            "/switch_shutdown": lambda: handle_set_switch_shutdown(
                self.hass, self.area_manager, area_id, data
            ),
            "/hysteresis": lambda: handle_set_area_hysteresis(
                self.hass, self.area_manager, area_id, data
            ),
            "/heating_type": lambda: handle_set_heating_type(
                self.hass, self.area_manager, area_id, data
            ),
            "/auto_preset": lambda: handle_set_auto_preset(
                self.hass, self.area_manager, area_id, data
            ),
            "/preset_config": lambda: handle_set_area_preset_config(
                self.hass, self.area_manager, area_id, data
            ),
            "/manual_override": lambda: handle_set_manual_override(
                self.hass, self.area_manager, area_id, data
            ),
            "/primary_temp_sensor": lambda: handle_set_primary_temperature_sensor(
                self.hass, self.area_manager, area_id, data
            ),
        }

        for suffix, handler in endpoint_handlers.items():
            if endpoint.endswith(suffix):
                return await handler()

        return None

    def _get_coordinator(self):
        """Get the coordinator instance from hass data.

        Returns:
            Coordinator instance or None
        """
        entry_ids = [
            key
            for key in self.hass.data[DOMAIN].keys()
            if key
            not in [
                "history",
                "climate_controller",
                "schedule_executor",
                "climate_unsub",
                "learning_engine",
                "area_logger",
                "vacation_manager",
                "safety_monitor",
                "config_manager",
                "user_manager",
                "comparison_engine",
            ]
        ]
        return self.hass.data[DOMAIN][entry_ids[0]] if entry_ids else None

    async def _handle_global_config_post(
        self, endpoint: str, data: dict
    ) -> web.Response | None:
        """Handle global configuration endpoints.

        Args:
            endpoint: Endpoint name
            data: Request body data

        Returns:
            Response if handled, None otherwise
        """
        handlers = {
            "frost_protection": lambda: handle_set_frost_protection(
                self.area_manager, data
            ),
            "history/config": lambda: handle_set_history_config(self.hass, data),
            "history/storage/migrate": lambda: handle_migrate_history_storage(
                self.hass, data
            ),
            "history/cleanup": lambda: handle_cleanup_history(self.hass),
            "global_presets": lambda: handle_set_global_presets(
                self.area_manager, data
            ),
            "global_presence": lambda: handle_set_global_presence(
                self.area_manager, data
            ),
            "hide_devices_panel": lambda: handle_set_hide_devices_panel(
                self.area_manager, data
            ),
            "config/advanced_control": lambda: handle_set_advanced_control_config(
                self.area_manager, data
            ),
            "vacation_mode": lambda: handle_enable_vacation_mode(self.hass, data),
            "safety_sensor": lambda: handle_set_safety_sensor(
                self.hass, self.area_manager, data
            ),
            "call_service": lambda: handle_call_service(self.hass, data),
        }

        handler = handlers.get(endpoint)
        if handler:
            return await handler()

        # Special cases with coordinator
        if endpoint == "hysteresis":
            coordinator = self._get_coordinator()
            return await handle_set_hysteresis_value(
                self.hass, self.area_manager, coordinator, data
            )
        elif endpoint == "opentherm_gateway":
            entry_ids = [
                entry.entry_id
                for entry in self.hass.config_entries.async_entries(DOMAIN)
            ]
            coordinator = self.hass.data[DOMAIN][entry_ids[0]] if entry_ids else None
            return await handle_set_opentherm_gateway(
                self.area_manager, coordinator, data
            )

        return None

    async def _handle_special_endpoints_post(
        self, request: web.Request, endpoint: str, data: dict
    ) -> web.Response | None:
        """Handle special endpoints (users, backups, comparison, opentherm).

        Args:
            request: Request object
            endpoint: Endpoint name
            data: Request body data

        Returns:
            Response if handled, None otherwise
        """
        # Import/Export endpoints
        if endpoint == "import":
            config_manager = self.hass.data[DOMAIN]["config_manager"]
            return await handle_import_config(self.hass, config_manager, data)
        elif endpoint == "validate":
            config_manager = self.hass.data[DOMAIN]["config_manager"]
            return await handle_validate_config(self.hass, config_manager, data)
        elif endpoint.startswith("backups/") and endpoint.endswith("/restore"):
            backup_filename = endpoint.split("/")[1]
            config_manager = self.hass.data[DOMAIN]["config_manager"]
            return await handle_restore_backup(
                self.hass, config_manager, backup_filename
            )

        # User endpoints
        elif endpoint == "users":
            user_manager = self.hass.data[DOMAIN]["user_manager"]
            return await handle_create_user(self.hass, user_manager, request)
        elif endpoint.startswith(_USERS_PATH) and not endpoint.endswith("/settings"):
            user_id = endpoint.split("/")[1]
            user_manager = self.hass.data[DOMAIN]["user_manager"]
            return await handle_update_user(self.hass, user_manager, request, user_id)
        elif endpoint == f"{_USERS_PATH}settings":
            user_manager = self.hass.data[DOMAIN]["user_manager"]
            return await handle_update_user_settings(self.hass, user_manager, request)

        # Comparison endpoints
        elif endpoint == "comparison/custom":
            comparison_engine = self.hass.data[DOMAIN]["comparison_engine"]
            return await handle_get_custom_comparison(
                self.hass, comparison_engine, request
            )

        # OpenTherm endpoints
        elif endpoint == "opentherm/capabilities/discover":
            return await handle_discover_opentherm_capabilities(
                self.hass, self.area_manager
            )
        elif endpoint == "opentherm/logs/clear":
            return await handle_clear_opentherm_logs(self.hass)

        return None

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

            # Try area action endpoints (no body required)
            for action in ["enable", "disable", "hide", "unhide", "cancel_boost"]:
                response = await self._handle_area_action_post(endpoint, action)
                if response:
                    return response

            # Parse JSON for endpoints that need data
            data = await request.json()
            _LOGGER.debug("POST data: %s", data)

            # Try area endpoints with data
            response = await self._handle_area_data_post(endpoint, data)
            if response:
                return response

            # Try global config endpoints
            response = await self._handle_global_config_post(endpoint, data)
            if response:
                return response

            # Try special endpoints (users, backups, comparison, opentherm)
            response = await self._handle_special_endpoints_post(
                request, endpoint, data
            )
            if response:
                return response

            return web.json_response({"error": ERROR_UNKNOWN_ENDPOINT}, status=404)
        except Exception as err:
            _LOGGER.error("Error handling POST %s: %s", endpoint, err)
            return web.json_response({"error": str(err)}, status=500)

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
                # Get sensor_id from query parameter
                sensor_id = request.query.get("sensor_id")
                if not sensor_id:
                    return web.json_response(
                        {"error": "sensor_id query parameter is required"}, status=400
                    )
                return await handle_remove_safety_sensor(
                    self.hass, self.area_manager, sensor_id
                )
            elif endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/devices/" in endpoint:
                parts = endpoint.split("/")
                area_id = parts[1]
                device_id = parts[3]
                return await handle_remove_device(self.area_manager, area_id, device_id)
            elif (
                endpoint.startswith(ENDPOINT_PREFIX_AREAS) and "/schedules/" in endpoint
            ):
                parts = endpoint.split("/")
                area_id = parts[1]
                schedule_id = parts[3]
                return await handle_remove_schedule(
                    self.hass, self.area_manager, area_id, schedule_id
                )
            elif (
                endpoint.startswith(ENDPOINT_PREFIX_AREAS)
                and "/window_sensors/" in endpoint
            ):
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await handle_remove_window_sensor(
                    self.hass, self.area_manager, area_id, entity_id
                )
            elif (
                endpoint.startswith(ENDPOINT_PREFIX_AREAS)
                and "/presence_sensors/" in endpoint
            ):
                parts = endpoint.split("/")
                area_id = parts[1]
                entity_id = "/".join(parts[3:])  # Reconstruct entity_id
                return await handle_remove_presence_sensor(
                    self.hass, self.area_manager, area_id, entity_id
                )
            # User endpoints
            elif endpoint.startswith(_USERS_PATH):
                user_id = endpoint.split("/")[1]
                user_manager = self.hass.data[DOMAIN]["user_manager"]
                return await handle_delete_user(
                    self.hass, user_manager, request, user_id
                )
            else:
                return web.json_response({"error": ERROR_UNKNOWN_ENDPOINT}, status=404)
        except Exception as err:
            _LOGGER.error("Error handling DELETE %s: %s", endpoint, err)
            return web.json_response({"error": str(err)}, status=500)


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
        frontend_path = self.hass.config.path(
            "custom_components/smart_heating/frontend/dist"
        )
        index_path = os.path.join(frontend_path, "index.html")

        try:
            async with aiofiles.open(index_path, "r", encoding="utf-8") as f:
                html_content = await f.read()

            # Fix asset paths to be relative to our endpoint
            html_content = html_content.replace('src="/', 'src="/smart_heating_static/')
            html_content = html_content.replace(
                'href="/', 'href="/smart_heating_static/'
            )

            return web.Response(
                text=html_content, content_type="text/html", charset="utf-8"
            )
        except FileNotFoundError:
            _LOGGER.error("Frontend build not found at %s", frontend_path)
            return web.Response(
                text="<h1>Frontend not built</h1><p>Run: cd frontend && npm run build</p>",
                content_type="text/html",
                status=500,
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
        import mimetypes
        import os

        # Path to the built frontend
        frontend_path = self.hass.config.path(
            "custom_components/smart_heating/frontend/dist"
        )
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

            return web.Response(body=content, content_type=content_type)
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
