"""Device control for climate system."""

import logging
from typing import Any, Optional

from homeassistant.components.climate.const import (
    DOMAIN as CLIMATE_DOMAIN,
)
from homeassistant.components.climate.const import (
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..models import Area

_LOGGER = logging.getLogger(__name__)


class DeviceControlHandler:
    """Handle device control operations (thermostats, switches, valves)."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager):
        """Initialize device control handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
        """
        self.hass = hass
        self.area_manager = area_manager
        self._device_capabilities = {}  # Cache for device capabilities
        self._last_set_temperatures = {}  # Cache last set temperature per thermostat

    def is_any_thermostat_actively_heating(self, area: Area) -> bool:
        """Check if any thermostat in the area is actively heating.

        This checks the hvac_action attribute to determine actual heating state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "heating"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "heating":
                return True
        return False

    def is_any_thermostat_actively_cooling(self, area: Area) -> bool:
        """Check if any thermostat in the area is actively cooling.

        This checks the hvac_action attribute to determine actual cooling state.

        Args:
            area: Area instance

        Returns:
            True if any thermostat reports hvac_action == "cooling"
        """
        thermostats = area.get_thermostats()
        for thermostat_id in thermostats:
            state = self.hass.states.get(thermostat_id)
            if state and state.attributes.get("hvac_action") == "cooling":
                return True
        return False

    def get_valve_capability(self, entity_id: str) -> dict[str, Any]:
        """Get valve control capabilities from HA entity.

        Works with ANY valve from ANY manufacturer by querying entity attributes.

        Args:
            entity_id: Entity ID of the valve

        Returns:
            Dict with capability information
        """
        # Check cache first
        if entity_id in self._device_capabilities:
            return self._device_capabilities[entity_id]

        capabilities = {
            "supports_position": False,
            "supports_temperature": False,
            "position_min": 0,
            "position_max": 100,
            "entity_domain": entity_id.split(".")[0] if "." in entity_id else "unknown",
        }

        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning(
                "Cannot determine capabilities for %s: entity not found", entity_id
            )
            self._device_capabilities[entity_id] = capabilities
            return capabilities

        # Check entity domain
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        capabilities["entity_domain"] = domain

        if domain == "number":
            # number.* entities support position control
            capabilities["supports_position"] = True
            capabilities["position_min"] = state.attributes.get("min", 0)
            capabilities["position_max"] = state.attributes.get("max", 100)
            _LOGGER.debug(
                "Valve %s supports position control (range: %s-%s)",
                entity_id,
                capabilities["position_min"],
                capabilities["position_max"],
            )

        elif domain == "climate":
            # climate.* entities - check if they have position attribute
            if "position" in state.attributes:
                capabilities["supports_position"] = True
                _LOGGER.debug(
                    "Valve %s (climate) supports position control via attribute",
                    entity_id,
                )

            # Check if it supports temperature
            if (
                "temperature" in state.attributes
                or "target_temp_low" in state.attributes
            ):
                capabilities["supports_temperature"] = True
                _LOGGER.debug("Valve %s supports temperature control", entity_id)

        # Cache the result
        self._device_capabilities[entity_id] = capabilities
        return capabilities

    async def _async_ensure_climate_power_on(self, climate_entity_id: str) -> None:
        """Ensure climate device power switch is on if it exists.

        Some AC units have separate power switches (e.g., switch.xxx_power).
        This method checks for common patterns and turns on the switch if found.

        Args:
            climate_entity_id: Climate entity ID (e.g., climate.air_conditioning_air_care)
        """
        # Extract base name from climate entity
        # climate.air_conditioning_air_care -> air_conditioning_air_care
        if "." not in climate_entity_id:
            return

        base_name = climate_entity_id.split(".", 1)[1]

        # Check for common power switch patterns
        power_switch_patterns = [
            f"switch.{base_name}_power",  # switch.air_conditioning_air_care_power
            f"switch.{base_name}_switch",
            f"switch.{base_name}",
        ]

        for switch_id in power_switch_patterns:
            state = self.hass.states.get(switch_id)
            if state:
                # Found a power switch, ensure it's on
                if state.state != "on":
                    _LOGGER.info(
                        "Turning on power switch %s for climate entity %s",
                        switch_id,
                        climate_entity_id,
                    )
                    await self.hass.services.async_call(
                        "switch",
                        "turn_on",
                        {"entity_id": switch_id},
                        blocking=False,
                    )
                else:
                    _LOGGER.debug(
                        "Power switch %s already on for %s",
                        switch_id,
                        climate_entity_id,
                    )
                return  # Found and handled the switch

        # No power switch found, which is normal for most thermostats
        _LOGGER.debug("No power switch found for %s", climate_entity_id)

    async def _async_turn_off_climate_power(self, climate_entity_id: str) -> None:
        """Turn off climate device power switch if it exists.

        Args:
            climate_entity_id: Climate entity ID
        """
        # Extract base name from climate entity
        if "." not in climate_entity_id:
            return

        base_name = climate_entity_id.split(".", 1)[1]

        # Check for common power switch patterns
        power_switch_patterns = [
            f"switch.{base_name}_power",
            f"switch.{base_name}_switch",
            f"switch.{base_name}",
        ]

        for switch_id in power_switch_patterns:
            state = self.hass.states.get(switch_id)
            if state:
                # Found a power switch, turn it off
                if state.state == "on":
                    _LOGGER.info(
                        "Turning off power switch %s for climate entity %s",
                        switch_id,
                        climate_entity_id,
                    )
                    await self.hass.services.async_call(
                        "switch",
                        "turn_off",
                        {"entity_id": switch_id},
                        blocking=False,
                    )
                return  # Found and handled the switch

    async def async_control_thermostats(
        self,
        area: Area,
        heating: bool,
        target_temp: Optional[float],
        hvac_mode: str = "heat",
    ) -> None:
        """Control thermostats in an area.

        Args:
            area: Area to control
            heating: Whether heating/cooling should be active
            target_temp: Target temperature
            hvac_mode: HVAC mode ("heat" or "cool")
        """
        from ..const import HVAC_MODE_COOL, HVAC_MODE_HEAT

        thermostats = area.get_thermostats()

        for thermostat_id in thermostats:
            try:
                if heating and target_temp is not None:
                    # First, check for and turn on associated power switch
                    # Some AC units have a separate power switch (e.g., switch.xxx_power)
                    await self._async_ensure_climate_power_on(thermostat_id)

                    # Set HVAC mode first
                    ha_hvac_mode = (
                        HVAC_MODE_HEAT if hvac_mode == "heat" else HVAC_MODE_COOL
                    )
                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        "set_hvac_mode",
                        {
                            "entity_id": thermostat_id,
                            "hvac_mode": ha_hvac_mode,
                        },
                        blocking=False,
                    )
                    _LOGGER.debug(
                        "Set thermostat %s to %s mode", thermostat_id, hvac_mode
                    )

                    # Only set temperature if it has changed (avoid API rate limiting)
                    last_temp = self._last_set_temperatures.get(thermostat_id)
                    if last_temp is None or abs(last_temp - target_temp) >= 0.1:
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            {
                                "entity_id": thermostat_id,
                                ATTR_TEMPERATURE: target_temp,
                            },
                            blocking=False,
                        )
                        self._last_set_temperatures[thermostat_id] = target_temp
                        _LOGGER.debug(
                            "Set thermostat %s to %.1f°C (%s mode)",
                            thermostat_id,
                            target_temp,
                            hvac_mode,
                        )
                    else:
                        _LOGGER.debug(
                            "Skipping thermostat %s update - already at %.1f°C",
                            thermostat_id,
                            target_temp,
                        )
                elif target_temp is not None:
                    # Update target temperature even when not heating/cooling
                    last_temp = self._last_set_temperatures.get(thermostat_id)
                    if last_temp is None or abs(last_temp - target_temp) >= 0.1:
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            {
                                "entity_id": thermostat_id,
                                ATTR_TEMPERATURE: target_temp,
                            },
                            blocking=False,
                        )
                        self._last_set_temperatures[thermostat_id] = target_temp
                        _LOGGER.debug(
                            "Updated thermostat %s target to %.1f°C (idle)",
                            thermostat_id,
                            target_temp,
                        )
                else:
                    # Turn off heating/cooling completely
                    if thermostat_id in self._last_set_temperatures:
                        del self._last_set_temperatures[thermostat_id]

                    try:
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_TURN_OFF,
                            {"entity_id": thermostat_id},
                            blocking=False,
                        )
                        _LOGGER.debug("Turned off thermostat %s", thermostat_id)

                        # Also turn off associated power switch if it exists
                        await self._async_turn_off_climate_power(thermostat_id)

                    except Exception:
                        # Fall back to minimum temperature if turn_off not supported
                        min_temp = 5.0
                        if self.area_manager.frost_protection_enabled:
                            min_temp = self.area_manager.frost_protection_temp

                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            {
                                "entity_id": thermostat_id,
                                ATTR_TEMPERATURE: min_temp,
                            },
                            blocking=False,
                        )
                        _LOGGER.debug(
                            "Thermostat %s doesn't support turn_off, set to %.1f°C",
                            thermostat_id,
                            min_temp,
                        )
            except Exception as err:
                _LOGGER.error("Failed to control thermostat %s: %s", thermostat_id, err)

    async def async_control_switches(self, area: Area, heating: bool) -> None:
        """Control switches (pumps, relays) in an area."""
        switches = area.get_switches()

        # Check if any thermostat is still actively heating
        thermostats_still_heating = self.is_any_thermostat_actively_heating(area)

        for switch_id in switches:
            try:
                if heating:
                    await self.hass.services.async_call(
                        "switch",
                        SERVICE_TURN_ON,
                        {"entity_id": switch_id},
                        blocking=False,
                    )
                    _LOGGER.debug("Turned on switch %s", switch_id)
                else:
                    # Keep switch on if thermostats still heating
                    if thermostats_still_heating:
                        _LOGGER.info(
                            "Area %s: Target reached but thermostat still heating - keeping switch %s ON",
                            area.area_id,
                            switch_id,
                        )
                        await self.hass.services.async_call(
                            "switch",
                            SERVICE_TURN_ON,
                            {"entity_id": switch_id},
                            blocking=False,
                        )
                    elif area.shutdown_switches_when_idle:
                        await self.hass.services.async_call(
                            "switch",
                            SERVICE_TURN_OFF,
                            {"entity_id": switch_id},
                            blocking=False,
                        )
                        _LOGGER.debug("Turned off switch %s", switch_id)
                    else:
                        _LOGGER.debug(
                            "Keeping switch %s on (shutdown_switches_when_idle=False)",
                            switch_id,
                        )
            except Exception as err:
                _LOGGER.error("Failed to control switch %s: %s", switch_id, err)

    async def async_control_valves(
        self, area: Area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valves/TRVs in an area."""
        valves = area.get_valves()

        for valve_id in valves:
            try:
                capabilities = self.get_valve_capability(valve_id)

                # Prefer position control if available
                if capabilities["supports_position"]:
                    domain = capabilities["entity_domain"]

                    if domain == "number":
                        # Direct position control via number entity
                        if heating:
                            await self.hass.services.async_call(
                                "number",
                                "set_value",
                                {
                                    "entity_id": valve_id,
                                    "value": capabilities["position_max"],
                                },
                                blocking=False,
                            )
                            _LOGGER.debug(
                                "Opened valve %s to %.0f%%",
                                valve_id,
                                capabilities["position_max"],
                            )
                        else:
                            await self.hass.services.async_call(
                                "number",
                                "set_value",
                                {
                                    "entity_id": valve_id,
                                    "value": capabilities["position_min"],
                                },
                                blocking=False,
                            )
                            _LOGGER.debug(
                                "Closed valve %s to %.0f%%",
                                valve_id,
                                capabilities["position_min"],
                            )

                    elif (
                        domain == "climate"
                        and "position" in self.hass.states.get(valve_id).attributes
                    ):
                        position = (
                            capabilities["position_max"]
                            if heating
                            else capabilities["position_min"]
                        )
                        try:
                            await self.hass.services.async_call(
                                CLIMATE_DOMAIN,
                                "set_position",
                                {
                                    "entity_id": valve_id,
                                    "position": position,
                                },
                                blocking=False,
                            )
                            _LOGGER.debug(
                                "Set valve %s position to %.0f%%", valve_id, position
                            )
                        except Exception:
                            _LOGGER.debug(
                                "Valve %s doesn't support set_position, using temperature control",
                                valve_id,
                            )
                            capabilities["supports_position"] = False
                            capabilities["supports_temperature"] = True

                # Fall back to temperature control
                if (
                    not capabilities["supports_position"]
                    and capabilities["supports_temperature"]
                ):
                    if heating and target_temp is not None:
                        offset = self.area_manager.trv_temp_offset
                        heating_temp = max(
                            target_temp + offset, self.area_manager.trv_heating_temp
                        )
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            {
                                "entity_id": valve_id,
                                ATTR_TEMPERATURE: heating_temp,
                            },
                            blocking=False,
                        )
                        _LOGGER.debug(
                            "Set TRV %s to heating temp %.1f°C", valve_id, heating_temp
                        )
                    else:
                        idle_temp = self.area_manager.trv_idle_temp
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_SET_TEMPERATURE,
                            {
                                "entity_id": valve_id,
                                ATTR_TEMPERATURE: idle_temp,
                            },
                            blocking=False,
                        )
                        _LOGGER.debug(
                            "Set TRV %s to idle temp %.1f°C", valve_id, idle_temp
                        )

                if (
                    not capabilities["supports_position"]
                    and not capabilities["supports_temperature"]
                ):
                    _LOGGER.warning(
                        "Valve %s doesn't support position or temperature control",
                        valve_id,
                    )

            except Exception as err:
                _LOGGER.error("Failed to control valve %s: %s", valve_id, err)

    async def async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control the global OpenTherm gateway based on aggregated demands."""
        if not self.area_manager.opentherm_enabled:
            return

        gateway_id = self.area_manager.opentherm_gateway_id
        if not gateway_id:
            return

        # Get OpenTherm logger from hass.data
        from ..const import DOMAIN

        opentherm_logger = self.hass.data.get(DOMAIN, {}).get("opentherm_logger")

        try:
            # Collect heating areas and their types for logging
            heating_area_ids = []
            heating_types = {}  # area_id -> heating_type
            overhead_temps = {}  # area_id -> overhead_temp

            if any_heating:
                for area_id, area in self.area_manager.get_all_areas().items():
                    if area.state == "heating":
                        heating_area_ids.append(area_id)
                        heating_types[area_id] = area.heating_type

                        # Calculate overhead for this area
                        if area.custom_overhead_temp is not None:
                            overhead_temps[area_id] = area.custom_overhead_temp
                        elif area.heating_type == "floor_heating":
                            overhead_temps[area_id] = 10.0  # Default for floor heating
                        else:  # radiator
                            overhead_temps[area_id] = 20.0  # Default for radiator

                        # Log individual zone demand
                        if opentherm_logger and area.current_temperature is not None:
                            opentherm_logger.log_zone_demand(
                                area_id=area_id,
                                area_name=area.name,
                                heating=True,
                                current_temp=area.current_temperature,
                                target_temp=area.target_temperature,
                            )

            # Control boiler
            if any_heating:
                # Calculate overhead based on heating types
                # Use the highest overhead for safety (fastest heating requirement)
                overhead = max(overhead_temps.values()) if overhead_temps else 20.0
                boiler_setpoint = max_target_temp + overhead

                # Determine heating type breakdown for logging
                floor_heating_count = sum(
                    1 for ht in heating_types.values() if ht == "floor_heating"
                )
                radiator_count = sum(
                    1 for ht in heating_types.values() if ht == "radiator"
                )

                # Use OpenTherm Gateway specific service instead of climate.set_temperature
                # The OTGW integration doesn't support set_temperature, use set_control_setpoint
                try:
                    await self.hass.services.async_call(
                        "opentherm_gw",
                        "set_control_setpoint",
                        {
                            "gateway_id": gateway_id.split(".")[-1].replace(
                                "_otgw_thermostat", ""
                            ),
                            "temperature": boiler_setpoint,
                        },
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to set OpenTherm Gateway control setpoint: %s. "
                        "Trying alternative MQTT method...",
                        err,
                    )
                    # Fallback: Try MQTT publish if service doesn't exist
                    # Extract gateway name from entity_id (e.g., climate.otgw_thermostat -> otgw)
                    try:
                        gateway_name = gateway_id.split(".")[-1].split("_")[0]
                        await self.hass.services.async_call(
                            "mqtt",
                            "publish",
                            {
                                "topic": f"opentherm/{gateway_name}/set/control_setpoint",
                                "payload": str(boiler_setpoint),
                            },
                            blocking=False,
                        )
                    except Exception as mqtt_err:
                        _LOGGER.error("MQTT fallback also failed: %s", mqtt_err)

                _LOGGER.info(
                    "OpenTherm gateway: Boiler ON, setpoint=%.1f°C (overhead=%.1f°C, %d floor heating, %d radiator)",
                    boiler_setpoint,
                    overhead,
                    floor_heating_count,
                    radiator_count,
                )

                # Log boiler control with heating type context
                if opentherm_logger:
                    opentherm_logger.log_boiler_control(
                        state="ON",
                        setpoint=boiler_setpoint,
                        heating_areas=heating_area_ids,
                        max_target_temp=max_target_temp,
                        overhead=overhead,
                        floor_heating_count=floor_heating_count,
                        radiator_count=radiator_count,
                    )
            else:
                # Turn off boiler by setting control setpoint to 0
                try:
                    await self.hass.services.async_call(
                        "opentherm_gw",
                        "set_control_setpoint",
                        {
                            "gateway_id": gateway_id.split(".")[-1].replace(
                                "_otgw_thermostat", ""
                            ),
                            "temperature": 0,
                        },
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to turn off OpenTherm Gateway: %s. Trying MQTT...", err
                    )
                    try:
                        gateway_name = gateway_id.split(".")[-1].split("_")[0]
                        await self.hass.services.async_call(
                            "mqtt",
                            "publish",
                            {
                                "topic": f"opentherm/{gateway_name}/set/control_setpoint",
                                "payload": "0",
                            },
                            blocking=False,
                        )
                    except Exception as mqtt_err:
                        _LOGGER.error("MQTT fallback also failed: %s", mqtt_err)

                _LOGGER.info("OpenTherm gateway: Boiler OFF")

                # Log boiler control
                if opentherm_logger:
                    opentherm_logger.log_boiler_control(
                        state="OFF",
                        heating_areas=[],
                    )

            # Get and log modulation status
            if opentherm_logger:
                gateway_state = self.hass.states.get(gateway_id)
                if gateway_state and gateway_state.state != "unavailable":
                    attrs = gateway_state.attributes
                    opentherm_logger.log_modulation(
                        modulation_level=attrs.get("relative_mod_level"),
                        flame_on=attrs.get("flame_on"),
                        ch_water_temp=attrs.get("ch_water_temp"),
                        control_setpoint=attrs.get("control_setpoint"),
                        boiler_water_temp=attrs.get("boiler_water_temp"),
                    )

        except Exception as err:
            _LOGGER.error("Failed to control OpenTherm gateway %s: %s", gateway_id, err)
