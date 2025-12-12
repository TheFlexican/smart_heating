"""OpenTherm Gateway logging for Smart Heating."""

# Lightweight logging utilities; skip coverage for some paths that are exercised in integration tests
# pragma: no cover

import logging
from collections import deque
from datetime import datetime
from typing import Any, Optional

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Maximum log entries in memory
MAX_LOG_ENTRIES = 500


class OpenThermLogger:
    """Logger for tracking OpenTherm Gateway operations.

    Tracks boiler control decisions, zone demands, temperature setpoints,
    modulation levels, and gateway capabilities.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the OpenTherm logger.

        Args:
            hass: Home Assistant instance
        """
        self._hass = hass
        self._logs: deque = deque(maxlen=MAX_LOG_ENTRIES)
        self._gateway_capabilities: dict[str, Any] = {}
        _LOGGER.info("OpenTherm logger initialized")

    def log_event(
        self,
        event_type: str,
        data: dict[str, Any],
        message: Optional[str] = None,
    ) -> None:
        """Log an OpenTherm event.

        Args:
            event_type: Type of event (boiler_control, zone_demand, modulation, gateway_info)
            data: Event data dictionary
            message: Optional human-readable message
        """
        timestamp = datetime.now().isoformat()

        entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
        }

        if message:
            entry["message"] = message

        self._logs.append(entry)

        # Also log to HA logger for debugging
        _LOGGER.debug("OpenTherm event [%s]: %s", event_type, message or data)

    def log_boiler_control(
        self,
        state: str,
        setpoint: Optional[float] = None,
        heating_areas: Optional[list[str]] = None,
        max_target_temp: Optional[float] = None,
        overhead: Optional[float] = None,
        floor_heating_count: Optional[int] = None,
        radiator_count: Optional[int] = None,
    ) -> None:
        """Log boiler control decision.

        Args:
            state: Boiler state (ON/OFF)
            setpoint: Temperature setpoint sent to boiler (°C)
            heating_areas: List of area IDs requesting heat
            max_target_temp: Highest target temperature across areas (°C)
            overhead: Overhead temperature used (°C)
            floor_heating_count: Number of floor heating zones active
            radiator_count: Number of radiator zones active
        """
        data = self._build_boiler_control_data(
            state,
            setpoint,
            heating_areas,
            max_target_temp,
            overhead,
            floor_heating_count,
            radiator_count,
        )
        message = self._build_boiler_control_message(
            state,
            setpoint,
            heating_areas,
            overhead,
            floor_heating_count,
            radiator_count,
        )
        self.log_event("boiler_control", data, message)

    def _build_boiler_control_data(
        self,
        state: str,
        setpoint: Optional[float] = None,
        heating_areas: Optional[list[str]] = None,
        max_target_temp: Optional[float] = None,
        overhead: Optional[float] = None,
        floor_heating_count: Optional[int] = None,
        radiator_count: Optional[int] = None,
    ) -> dict[str, Any]:
        data = {"state": state}
        if setpoint is not None:
            data["setpoint"] = round(setpoint, 1)
        if heating_areas is not None:
            data["heating_areas"] = heating_areas
            data["num_heating_areas"] = len(heating_areas)
        if max_target_temp is not None:
            data["max_target_temp"] = round(max_target_temp, 1)
        if overhead is not None:
            data["overhead"] = round(overhead, 1)
        if floor_heating_count is not None:
            data["floor_heating_count"] = floor_heating_count
        if radiator_count is not None:
            data["radiator_count"] = radiator_count
        return data

    def _build_boiler_control_message(
        self,
        state: str,
        setpoint: Optional[float] = None,
        heating_areas: Optional[list[str]] = None,
        overhead: Optional[float] = None,
        floor_heating_count: Optional[int] = None,
        radiator_count: Optional[int] = None,
    ) -> str:
        if state != "ON":
            return "Boiler OFF - No heating demand"
        parts = [f"Boiler ON - Setpoint: {setpoint:.1f}°C"]
        if overhead is not None:
            parts.append(f"overhead +{overhead:.0f}°C")
        if floor_heating_count is not None and radiator_count is not None:
            zone_info = []
            if floor_heating_count > 0:
                zone_info.append(f"{floor_heating_count} floor heating")
            if radiator_count > 0:
                zone_info.append(f"{radiator_count} radiator")
            if zone_info:
                parts.append(" + ".join(zone_info))
        elif heating_areas:
            parts.append(f"{len(heating_areas)} zone(s)")
        return " | ".join(parts)

    def log_zone_demand(
        self,
        area_id: str,
        area_name: str,
        heating: bool,
        current_temp: float,
        target_temp: float,
    ) -> None:
        """Log zone heating demand.

        Args:
            area_id: Area identifier
            area_name: Human-readable area name
            heating: Whether area is requesting heat
            current_temp: Current temperature (°C)
            target_temp: Target temperature (°C)
        """
        data = {
            "area_id": area_id,
            "area_name": area_name,
            "heating": heating,
            "current_temp": round(current_temp, 1),
            "target_temp": round(target_temp, 1),
            "temp_diff": round(target_temp - current_temp, 1),
        }

        message = f"{area_name}: {'HEATING' if heating else 'IDLE'} ({current_temp:.1f}°C → {target_temp:.1f}°C)"

        self.log_event("zone_demand", data, message)

    def log_modulation(
        self,
        modulation_level: Optional[float] = None,
        flame_on: Optional[bool] = None,
        ch_water_temp: Optional[float] = None,
        control_setpoint: Optional[float] = None,
        boiler_water_temp: Optional[float] = None,
    ) -> None:
        """Log modulation status from OpenTherm Gateway.

        Args:
            modulation_level: Current modulation percentage (0-100%)
            flame_on: Whether flame is active
            ch_water_temp: Central heating water temperature (°C)
            control_setpoint: Control setpoint temperature (°C)
            boiler_water_temp: Boiler water temperature (°C)
        """
        data = {}

        if modulation_level is not None:
            data["modulation_level"] = round(modulation_level, 1)

        if flame_on is not None:
            data["flame_on"] = flame_on

        if ch_water_temp is not None:
            data["ch_water_temp"] = round(ch_water_temp, 1)

        if control_setpoint is not None:
            data["control_setpoint"] = round(control_setpoint, 1)

        if boiler_water_temp is not None:
            data["boiler_water_temp"] = round(boiler_water_temp, 1)

        # Build message
        parts = []
        if modulation_level is not None:
            parts.append(f"Modulation: {modulation_level:.1f}%")
        if flame_on is not None:
            parts.append(f"Flame: {'ON' if flame_on else 'OFF'}")
        if ch_water_temp is not None:
            parts.append(f"CH Water: {ch_water_temp:.1f}°C")

        message = " | ".join(parts) if parts else "Modulation status"

        self.log_event("modulation", data, message)

    def log_gateway_info(
        self,
        gateway_id: str,
        enabled: bool,
        available: bool = False,
        capabilities: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log gateway information and capabilities.

        Args:
            gateway_id: Gateway entity ID
            enabled: Whether OpenTherm control is enabled
            available: Whether gateway is available
            capabilities: Gateway capabilities from MQTT discovery
        """
        data = {
            "gateway_id": gateway_id,
            "enabled": enabled,
            "available": available,
        }

        if capabilities:
            data["capabilities"] = capabilities
            self._gateway_capabilities = capabilities

        message = f"Gateway: {gateway_id} | Enabled: {enabled} | Available: {available}"

        self.log_event("gateway_info", data, message)

    def get_logs(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Get OpenTherm logs.

        Args:
            limit: Maximum number of entries to return (None = all)

        Returns:
            List of log entries (newest first)
        """
        logs = list(self._logs)
        logs.reverse()  # Newest first

        if limit:
            logs = logs[:limit]

        return logs

    def get_gateway_capabilities(self) -> dict[str, Any]:
        """Get stored gateway capabilities.

        Returns:
            Dictionary of gateway capabilities
        """
        return self._gateway_capabilities.copy()

    def clear_logs(self) -> None:
        """Clear all logs."""
        self._logs.clear()
        _LOGGER.info("OpenTherm logs cleared")

    async def async_discover_mqtt_capabilities(  # NOSONAR
        self, gateway_entity_id: str
    ) -> dict[str, Any]:
        """Discover OpenTherm Gateway capabilities via MQTT.

        Args:
            gateway_entity_id: Entity ID of the gateway

        Returns:
            Dictionary of discovered capabilities
        """
        try:
            # Get entity state
            state = self._hass.states.get(gateway_entity_id)
            if not state:
                _LOGGER.warning("Gateway entity %s not found", gateway_entity_id)
                return {}

            # Extract capabilities from entity attributes
            capabilities = {
                "entity_id": gateway_entity_id,
                "state": state.state,
                "available": state.state != "unavailable",
                "attributes": {},
            }

            # Collect relevant attributes
            relevant_attrs = [
                "current_temperature",
                "temperature",
                "target_temp",
                "hvac_action",
                "hvac_mode",
                "hvac_modes",
                "min_temp",
                "max_temp",
                "temp_step",
                # OpenTherm specific
                "boiler_water_temp",
                "ch_water_temp",
                "control_setpoint",
                "flame_on",
                "modulation_level",
                "relative_mod_level",
                "max_relative_mod_level",
                "otgw_about",
                "otgw_build",
                "otgw_clockmhz",
                "otgw_mode",
                "master_ch_enabled",
                "master_dhw_enabled",
                "slave_ch_active",
                "slave_dhw_active",
            ]

            for attr in relevant_attrs:
                if attr in state.attributes:
                    capabilities["attributes"][attr] = state.attributes[attr]

            # Log capabilities
            self.log_gateway_info(
                gateway_id=gateway_entity_id,
                enabled=True,
                available=capabilities["available"],
                capabilities=capabilities,
            )

            _LOGGER.info(
                "Discovered OpenTherm Gateway capabilities: %d attributes",
                len(capabilities["attributes"]),
            )

            return capabilities

        except Exception as err:
            _LOGGER.error(
                "Failed to discover MQTT capabilities for %s: %s",
                gateway_entity_id,
                err,
            )
            return {}
