"""Device control for climate system."""
import logging
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.components.climate.const import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)

from ..models import Area
from ..area_manager import AreaManager

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
            'supports_position': False,
            'supports_temperature': False,
            'position_min': 0,
            'position_max': 100,
            'entity_domain': entity_id.split('.')[0] if '.' in entity_id else 'unknown'
        }
        
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Cannot determine capabilities for %s: entity not found", entity_id)
            self._device_capabilities[entity_id] = capabilities
            return capabilities
        
        # Check entity domain
        domain = entity_id.split('.')[0] if '.' in entity_id else ''
        capabilities['entity_domain'] = domain
        
        if domain == 'number':
            # number.* entities support position control
            capabilities['supports_position'] = True
            capabilities['position_min'] = state.attributes.get('min', 0)
            capabilities['position_max'] = state.attributes.get('max', 100)
            _LOGGER.debug(
                "Valve %s supports position control (range: %s-%s)",
                entity_id,
                capabilities['position_min'],
                capabilities['position_max']
            )
        
        elif domain == 'climate':
            # climate.* entities - check if they have position attribute
            if 'position' in state.attributes:
                capabilities['supports_position'] = True
                _LOGGER.debug("Valve %s (climate) supports position control via attribute", entity_id)
            
            # Check if it supports temperature
            if 'temperature' in state.attributes or 'target_temp_low' in state.attributes:
                capabilities['supports_temperature'] = True
                _LOGGER.debug("Valve %s supports temperature control", entity_id)
        
        # Cache the result
        self._device_capabilities[entity_id] = capabilities
        return capabilities

    async def async_control_thermostats(
        self, area: Area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control thermostats in an area."""
        thermostats = area.get_thermostats()
        
        for thermostat_id in thermostats:
            try:
                if heating and target_temp is not None:
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
                            "Set thermostat %s to %.1f°C", thermostat_id, target_temp
                        )
                    else:
                        _LOGGER.debug(
                            "Skipping thermostat %s update - already at %.1f°C",
                            thermostat_id, target_temp
                        )
                elif target_temp is not None:
                    # Update target temperature even when not heating
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
                            "Updated thermostat %s target to %.1f°C (idle)", thermostat_id, target_temp
                        )
                else:
                    # Turn off heating completely
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
                            thermostat_id, min_temp
                        )
            except Exception as err:
                _LOGGER.error(
                    "Failed to control thermostat %s: %s", 
                    thermostat_id, err
                )

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
                            area.area_id, switch_id
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
                        _LOGGER.debug("Keeping switch %s on (shutdown_switches_when_idle=False)", switch_id)
            except Exception as err:
                _LOGGER.error(
                    "Failed to control switch %s: %s",
                    switch_id, err
                )

    async def async_control_valves(
        self, area: Area, heating: bool, target_temp: Optional[float]
    ) -> None:
        """Control valves/TRVs in an area."""
        valves = area.get_valves()
        
        for valve_id in valves:
            try:
                capabilities = self.get_valve_capability(valve_id)
                
                # Prefer position control if available
                if capabilities['supports_position']:
                    domain = capabilities['entity_domain']
                    
                    if domain == 'number':
                        # Direct position control via number entity
                        if heating:
                            await self.hass.services.async_call(
                                "number",
                                "set_value",
                                {
                                    "entity_id": valve_id,
                                    "value": capabilities['position_max'],
                                },
                                blocking=False,
                            )
                            _LOGGER.debug(
                                "Opened valve %s to %.0f%%",
                                valve_id, capabilities['position_max']
                            )
                        else:
                            await self.hass.services.async_call(
                                "number",
                                "set_value",
                                {
                                    "entity_id": valve_id,
                                    "value": capabilities['position_min'],
                                },
                                blocking=False,
                            )
                            _LOGGER.debug(
                                "Closed valve %s to %.0f%%",
                                valve_id, capabilities['position_min']
                            )
                    
                    elif domain == 'climate' and 'position' in self.hass.states.get(valve_id).attributes:
                        position = capabilities['position_max'] if heating else capabilities['position_min']
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
                            _LOGGER.debug("Set valve %s position to %.0f%%", valve_id, position)
                        except Exception:
                            _LOGGER.debug(
                                "Valve %s doesn't support set_position, using temperature control",
                                valve_id
                            )
                            capabilities['supports_position'] = False
                            capabilities['supports_temperature'] = True
                
                # Fall back to temperature control
                if not capabilities['supports_position'] and capabilities['supports_temperature']:
                    if heating and target_temp is not None:
                        offset = self.area_manager.trv_temp_offset
                        heating_temp = max(target_temp + offset, self.area_manager.trv_heating_temp)
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
                            "Set TRV %s to heating temp %.1f°C", 
                            valve_id, heating_temp
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
                            "Set TRV %s to idle temp %.1f°C", 
                            valve_id, idle_temp
                        )
                
                if not capabilities['supports_position'] and not capabilities['supports_temperature']:
                    _LOGGER.warning(
                        "Valve %s doesn't support position or temperature control",
                        valve_id
                    )
                        
            except Exception as err:
                _LOGGER.error(
                    "Failed to control valve %s: %s",
                    valve_id, err
                )

    async def async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control the global OpenTherm gateway based on aggregated demands."""
        if not self.area_manager.opentherm_enabled:
            return
        
        gateway_id = self.area_manager.opentherm_gateway_id
        if not gateway_id:
            return
        
        try:
            if any_heating:
                boiler_setpoint = max_target_temp + 20
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_SET_TEMPERATURE,
                    {
                        "entity_id": gateway_id,
                        ATTR_TEMPERATURE: boiler_setpoint,
                    },
                    blocking=False,
                )
                _LOGGER.info(
                    "OpenTherm gateway: Boiler ON, setpoint=%.1f°C",
                    boiler_setpoint
                )
            else:
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_TURN_OFF,
                    {"entity_id": gateway_id},
                    blocking=False,
                )
                _LOGGER.info("OpenTherm gateway: Boiler OFF")
                
        except Exception as err:
            _LOGGER.error(
                "Failed to control OpenTherm gateway %s: %s",
                gateway_id, err
            )
