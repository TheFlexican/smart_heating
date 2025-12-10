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
from ..heating_curve import HeatingCurve
from ..pid import PID, Error
from ..pwm import PWM
from ..minimum_setpoint import MinimumSetpoint

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
        # Advanced controllers per area
        self._heating_curves: dict[str, HeatingCurve] = {}
        self._pids: dict[str, PID] = {}
        self._pwms: dict[str, PWM] = {}
        self._min_setpoints: dict[str, MinimumSetpoint] = {}

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
        # Only attempt control when a gateway ID is configured
        gateway_id = self.area_manager.opentherm_gateway_id
        if not gateway_id:
            return
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
                # Calculate basic overhead
                overhead = max(overhead_temps.values()) if overhead_temps else 20.0

                # Advanced control: compute heating curve / PID / PWM setpoints if enabled
                advanced_enabled = self.area_manager.advanced_control_enabled
                heating_curve_enabled = self.area_manager.heating_curve_enabled
                pid_enabled = self.area_manager.pid_enabled

                # Collect candidates per area
                setpoint_candidates = []
                for aid in heating_area_ids:
                    area = self.area_manager.get_area(aid)
                    if not area:
                        continue

                    # Determine outside temperature if available on area
                    outside_temp = None
                    if area.weather_entity_id:
                        ws = self.hass.states.get(area.weather_entity_id)
                        try:
                            outside_temp = (
                                float(ws.state)
                                if ws and ws.state not in ("unknown", "unavailable")
                                else None
                            )
                        except Exception:
                            outside_temp = None

                    # Default candidate: max target + overhead
                    candidate = area.target_temperature + overhead

                    # Heating curve
                    if advanced_enabled and heating_curve_enabled:
                        coefficient = (
                            area.heating_curve_coefficient
                            or self.area_manager.default_heating_curve_coefficient
                        )
                        hc = self._heating_curves.get(aid) or HeatingCurve(
                            heating_system=(
                                "underfloor"
                                if area.heating_type == "floor_heating"
                                else "radiator"
                            ),
                            coefficient=coefficient,
                        )
                        self._heating_curves[aid] = hc
                        if outside_temp is not None:
                            hc.update(area.target_temperature, outside_temp)
                            if hc.value is not None:
                                candidate = hc.value

                    # PID adjustment
                    if (
                        advanced_enabled
                        and pid_enabled
                        and area.current_temperature is not None
                    ):
                        pid = self._pids.get(aid)
                        if not pid:
                            pid = PID(
                                heating_system=area.heating_type,
                                automatic_gain_value=1.0,
                                heating_curve_coefficient=(
                                    area.heating_curve_coefficient
                                    or self.area_manager.default_heating_curve_coefficient
                                ),
                                automatic_gains=True,
                            )
                            self._pids[aid] = pid
                        err = area.target_temperature - (
                            area.current_temperature or 0.0
                        )
                        # Use heating curve value if available as heating_curve_value
                        hc_local = self._heating_curves.get(aid)
                        hv = (
                            hc_local.value
                            if hc_local and hc_local.value is not None
                            else None
                        )
                        pid_out = pid.update(Error(err), hv)
                        candidate = candidate + pid_out

                    setpoint_candidates.append(candidate)

                # Choose the highest candidate setpoint
                boiler_setpoint = (
                    max(setpoint_candidates)
                    if setpoint_candidates
                    else (max_target_temp + overhead)
                )

                # Minimum setpoint calculation
                # Get configured gateway id once
                gateway_device_id = self.area_manager.opentherm_gateway_id
                for aid in heating_area_ids:
                    area = self.area_manager.get_area(aid)
                    if not area:
                        continue
                    # Create or get existing MinimumSetpoint controller
                    minsp = self._min_setpoints.get(aid)
                    if not minsp:
                        # Use different minimum setpoint default depending on heating
                        # system type. Underfloor systems typically need higher flow
                        # temperatures than the old defaults; use conservative
                        # defaults that should result in faster heat-up times.
                        default_min = (
                            40.0 if area.heating_type == "floor_heating" else 55.0
                        )
                        minsp = MinimumSetpoint(
                            configured_minimum_setpoint=default_min,
                            adjustment_factor=1.0,
                        )
                        self._min_setpoints[aid] = minsp

                    # construct a minimal boiler_state object using gateway values
                    gateway_state = self.hass.states.get(gateway_device_id)
                    if gateway_state:
                        boiler_state = type("_b", (), {})()
                        boiler_state.return_temperature = gateway_state.attributes.get(
                            "return_water_temp"
                        ) or gateway_state.attributes.get("boiler_water_temp")
                        boiler_state.flow_temperature = gateway_state.attributes.get(
                            "ch_water_temp"
                        )
                        boiler_state.flame_active = gateway_state.attributes.get(
                            "flame_on"
                        )
                        boiler_state.setpoint = boiler_setpoint
                        minsp.calculate(boiler_state)
                        # Respect minimum setpoint
                        if (
                            minsp.current_minimum_setpoint is not None
                            and boiler_setpoint < minsp.current_minimum_setpoint
                        ):
                            _LOGGER.debug(
                                "Enforcing minimum setpoint: %.1f°C (was %.1f°C)",
                                minsp.current_minimum_setpoint,
                                boiler_setpoint,
                            )
                            boiler_setpoint = minsp.current_minimum_setpoint

                # Determine heating type breakdown for logging
                floor_heating_count = sum(
                    1 for ht in heating_types.values() if ht == "floor_heating"
                )
                radiator_count = sum(
                    1 for ht in heating_types.values() if ht == "radiator"
                )

                # Use OpenTherm Gateway integration service
                # Get gateway_id directly from area_manager configuration
                gateway_device_id = self.area_manager.opentherm_gateway_id

                if not gateway_device_id:
                    _LOGGER.error(
                        "OpenTherm Gateway ID not configured. "
                        "Please set it via Global Settings or service call: smart_heating.set_opentherm_gateway"
                    )
                    return

                try:
                    # Use the OpenTherm integration service directly and expect the
                    # configured gateway_id (slug) to be provided by options.
                    # If PWM is enabled and gateway does not support modulation, approximate duty using PWM
                    gateway_state = self.hass.states.get(gateway_device_id)
                    if (
                        self.area_manager.pwm_enabled
                        and gateway_state
                        and not gateway_state.attributes.get("relative_mod_level")
                    ):
                        # Very rough PWM approximation: set to setpoint if duty > 0.5, else 0.0
                        boiler_temp = gateway_state.attributes.get(
                            "boiler_water_temp"
                        ) or gateway_state.attributes.get("ch_water_temp")
                        try:
                            boiler_temp = float(boiler_temp)
                        except Exception:
                            boiler_temp = None

                        if boiler_temp is not None:
                            base_offset = (
                                20.0
                                if any(
                                    ht == "floor_heating"
                                    for ht in heating_types.values()
                                )
                                else 27.2
                            )
                            duty = (
                                (boiler_setpoint - base_offset)
                                / (boiler_temp - base_offset)
                                if (boiler_temp - base_offset) != 0
                                else 1.0
                            )
                            duty = min(max(duty, 0.0), 1.0)
                            if duty < 0.5:
                                _LOGGER.debug(
                                    "PWM approximation: duty=%.2f -> setpoint=0.0", duty
                                )
                                boiler_setpoint = 0.0
                            else:
                                _LOGGER.debug(
                                    "PWM approximation: duty=%.2f -> setpoint=%.1f",
                                    duty,
                                    boiler_setpoint,
                                )

                    await self.hass.services.async_call(
                        "opentherm_gw",
                        "set_control_setpoint",
                        {
                            "gateway_id": gateway_device_id,
                            "temperature": float(boiler_setpoint),
                        },
                        blocking=False,
                    )
                    _LOGGER.info(
                        "OpenTherm gateway: Set setpoint via gateway service (gateway_id=%s): %.1f°C",
                        gateway_device_id,
                        boiler_setpoint,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to set OpenTherm Gateway setpoint (gateway_id=%s): %s",
                        gateway_device_id,
                        err,
                    )

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
                # Turn off boiler by setting setpoint to 0
                gateway_device_id = self.area_manager.opentherm_gateway_id

                if not gateway_device_id:
                    _LOGGER.warning(
                        "OpenTherm Gateway ID not configured, cannot turn off"
                    )
                    return

                try:
                    await self.hass.services.async_call(
                        "opentherm_gw",
                        "set_control_setpoint",
                        {
                            "gateway_id": gateway_device_id,
                            "temperature": 0.0,
                        },
                        blocking=False,
                    )
                    _LOGGER.info(
                        "OpenTherm gateway: Boiler OFF (setpoint=0 via service, gateway_id=%s)",
                        gateway_device_id,
                    )
                except Exception as err:
                    _LOGGER.error(
                        "Failed to turn off OpenTherm Gateway (gateway_id=%s): %s",
                        gateway_device_id,
                        err,
                    )

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
