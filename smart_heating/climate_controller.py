"""Climate controller for Smart Heating."""
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.components.climate.const import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)

from .area_manager import AreaManager
from .models import Area
from .const import (
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_SWITCH,
    DEVICE_TYPE_VALVE,
)

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control heating based on area settings and schedules."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager, learning_engine=None) -> None:
        """Initialize the climate controller.
        
        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            learning_engine: Optional learning engine for adaptive features
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self._hysteresis = 0.5  # Temperature hysteresis in °C
        self._record_counter = 0  # Counter for history recording
        self._device_capabilities = {}  # Cache for device capabilities
        self._area_heating_events = {}  # Track active heating events per area
        self._last_set_temperatures = {}  # Cache last set temperature per thermostat to avoid unnecessary API calls

    def _get_valve_capability(self, entity_id: str) -> dict[str, Any]:
        """Get valve control capabilities from HA entity.
        
        IMPORTANT: This method uses ZERO hardcoded device models or manufacturers.
        It queries Home Assistant entity attributes at runtime to determine capabilities.
        Works with ANY valve from ANY manufacturer (TuYa, Danfoss, Eurotronic, Sonoff, etc.).
        
        Queries the entity's attributes and supported features to determine:
        - Whether it supports position control (via number.* or position attribute)
        - Whether it only supports temperature control
        - Min/max values for position control
        
        Args:
            entity_id: Entity ID of the valve
            
        Returns:
            Dict with capability information:
            {
                'supports_position': bool,
                'supports_temperature': bool,
                'position_min': float (if applicable),
                'position_max': float (if applicable),
                'entity_domain': str
            }
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
            
            # Check if it supports temperature (most climate entities do)
            if 'temperature' in state.attributes or 'target_temp_low' in state.attributes:
                capabilities['supports_temperature'] = True
                _LOGGER.debug("Valve %s supports temperature control", entity_id)
        
        # Cache the result
        self._device_capabilities[entity_id] = capabilities
        return capabilities

    async def async_update_area_temperatures(self) -> None:
        """Update current temperatures for all areas from sensors."""
        for area_id, area in self.area_manager.get_all_areas().items():
            # Get temperature sensors for this area
            temp_sensors = area.get_temperature_sensors()
            # Also include thermostats as temperature sources
            thermostats = area.get_thermostats()
            
            if not temp_sensors and not thermostats:
                continue
            
            # Calculate average temperature from all sensors
            temps = []
            
            # Read from temperature sensors
            for sensor_id in temp_sensors:
                state = self.hass.states.get(sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    try:
                        temp_value = float(state.state)
                        
                        # Check if temperature is in Fahrenheit and convert to Celsius
                        unit = state.attributes.get("unit_of_measurement", "°C")
                        if unit in ("°F", "F"):
                            temp_value = (temp_value - 32) * 5/9
                            _LOGGER.debug(
                                "Converted temperature from %s: %s°F -> %.1f°C",
                                sensor_id, state.state, temp_value
                            )
                        
                        temps.append(temp_value)
                    except (ValueError, TypeError):
                        _LOGGER.warning(
                            "Invalid temperature from %s: %s", 
                            sensor_id, state.state
                        )
            
            # Read from thermostats (use current_temperature attribute)
            for thermostat_id in thermostats:
                state = self.hass.states.get(thermostat_id)
                if state and state.state not in ("unknown", "unavailable"):
                    current_temp = state.attributes.get("current_temperature")
                    if current_temp is not None:
                        try:
                            temp_value = float(current_temp)
                            
                            # Check if temperature is in Fahrenheit and convert to Celsius
                            unit = state.attributes.get("unit_of_measurement", "°C")
                            if unit in ("°F", "F"):
                                temp_value = (temp_value - 32) * 5/9
                                _LOGGER.debug(
                                    "Converted temperature from thermostat %s: %.1f°F -> %.1f°C",
                                    thermostat_id, current_temp, temp_value
                                )
                            
                            temps.append(temp_value)
                        except (ValueError, TypeError):
                            _LOGGER.warning(
                                "Invalid current_temperature from thermostat %s: %s", 
                                thermostat_id, current_temp
                            )
            
            if temps:
                avg_temp = sum(temps) / len(temps)
                area.current_temperature = avg_temp
                _LOGGER.debug(
                    "Area %s temperature: %.1f°C (from %d sensors)",
                    area_id, avg_temp, len(temps)
                )

    async def _async_update_sensor_states(self) -> None:
        """Update window and presence sensor states for all areas."""
        for area_id, area in self.area_manager.get_all_areas().items():
            # Update window sensor states
            if area.window_sensors:
                any_window_open = False
                for sensor in area.window_sensors:
                    sensor_id = sensor.get("entity_id") if isinstance(sensor, dict) else sensor
                    state = self.hass.states.get(sensor_id)
                    if state:
                        # Binary sensors: on/open = window open
                        is_open = state.state in ("on", "open", "true", "True")
                        if is_open:
                            any_window_open = True
                            _LOGGER.debug("Window sensor %s is open in area %s", sensor_id, area_id)
                
                # Update cached state
                if area.window_is_open != any_window_open:
                    area.window_is_open = any_window_open
                    if any_window_open:
                        _LOGGER.info("Window(s) opened in area %s - temperature adjustment active", area_id)
                        if hasattr(self, 'area_logger') and self.area_logger:
                            self.area_logger.log_event(
                                area_id,
                                "sensor",
                                "Window opened - temperature adjustment active",
                                {"sensor_type": "window", "state": "open"}
                            )
                    else:
                        _LOGGER.info("All windows closed in area %s - normal heating resumed", area_id)
                        if hasattr(self, 'area_logger') and self.area_logger:
                            self.area_logger.log_event(
                                area_id,
                                "sensor",
                                "All windows closed - normal heating resumed",
                                {"sensor_type": "window", "state": "closed"}
                            )
            
            # Update presence sensor states
            # Use global presence sensors if enabled, otherwise use area-specific
            presence_sensors = []
            if area.use_global_presence:
                # Use global presence sensors
                presence_sensors = self.area_manager.global_presence_sensors
            else:
                # Use area-specific sensors
                presence_sensors = area.presence_sensors
            
            if presence_sensors:
                any_presence_detected = False
                for sensor in presence_sensors:
                    sensor_id = sensor.get("entity_id") if isinstance(sensor, dict) else sensor
                    state = self.hass.states.get(sensor_id)
                    if state:
                        # Binary sensors or motion sensors: on/home/detected = presence
                        is_present = state.state in ("on", "home", "detected", "true", "True")
                        if is_present:
                            any_presence_detected = True
                            _LOGGER.debug("Presence detected by %s in area %s", sensor_id, area_id)
                
                # Update cached state
                if area.presence_detected != any_presence_detected:
                    area.presence_detected = any_presence_detected
                    if any_presence_detected:
                        _LOGGER.info("Presence detected in area %s - temperature boost active", area_id)
                        if hasattr(self, 'area_logger') and self.area_logger:
                            self.area_logger.log_event(
                                area_id,
                                "sensor",
                                "Presence detected - temperature boost active",
                                {"sensor_type": "presence", "state": "detected"}
                            )
                    else:
                        _LOGGER.info("No presence in area %s - boost removed", area_id)
                        if hasattr(self, 'area_logger') and self.area_logger:
                            self.area_logger.log_event(
                                area_id,
                                "sensor",
                                "No presence detected - boost removed",
                                {"sensor_type": "presence", "state": "not_detected"}
                            )


    async def async_control_heating(self) -> None:
        """Control heating for all areas based on temperature and schedules."""
        from .const import DOMAIN
        
        current_time = datetime.now()
        
        # First update all temperatures
        await self.async_update_area_temperatures()
        
        # Update window and presence sensor states
        await self._async_update_sensor_states()
        
        # Check for expired boost modes
        for area in self.area_manager.get_all_areas().values():
            if area.boost_mode_active:
                area.check_boost_expiry()
        
        # Increment counter for history recording (every 10 cycles = 5 minutes)
        self._record_counter += 1
        should_record_history = (self._record_counter % 10 == 0)
        
        # Get history tracker if available
        history_tracker = self.hass.data.get(DOMAIN, {}).get("history")
        
        # Track heating demands across all areas for boiler control
        heating_areas = []
        max_target_temp = 0.0
        
        # Then control each area
        for area_id, area in self.area_manager.get_all_areas().items():
            # Record history for ALL areas (even disabled ones) - every 5 minutes
            if should_record_history and history_tracker and area.current_temperature is not None:
                await history_tracker.async_record_temperature(
                    area_id, 
                    area.current_temperature, 
                    area.target_temperature, 
                    area.state
                )
            
            if not area.enabled:
                # Area disabled - don't control any devices, just skip
                area.state = "off"  # Update area state
                
                # Log disabled state but still track temperature
                if hasattr(self, 'area_logger') and self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "mode",
                        "Area disabled - no device control, temperature tracking continues",
                        {
                            "mode": "disabled",
                            "current_temperature": area.current_temperature
                        }
                    )
                # Skip to next area - don't touch any devices
                continue
            
            # Check for manual override mode
            if hasattr(area, 'manual_override') and area.manual_override:
                _LOGGER.info(
                    "Area %s in MANUAL OVERRIDE mode - skipping thermostat control but managing switches",
                    area_id
                )
                area.state = "manual"  # Set state to manual
                if hasattr(self, 'area_logger') and self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "mode",
                        "Manual override mode active - user control",
                        {"mode": "manual_override"}
                    )
                
                # Still control switches/pumps based on actual heating state
                # Check if thermostat is actually heating
                is_heating = False
                for device_id, device_data in area.devices.items():
                    if device_data.get("type") == "thermostat":
                        state = self.hass.states.get(device_id)
                        if state and state.attributes.get("hvac_action") == "heating":
                            is_heating = True
                            break
                
                # Control switches based on actual heating state
                await self._async_control_switches(area, is_heating)
                
                # Skip rest of climate control logic
                continue
            
            # Check for vacation mode - override preset if active
            vacation_manager = self.hass.data.get("smart_heating", {}).get("vacation_manager")
            if vacation_manager and vacation_manager.is_active():
                vacation_preset = vacation_manager.get_preset_mode()
                if vacation_preset:
                    # Override area preset mode with vacation preset
                    area.preset_mode = vacation_preset
                    _LOGGER.debug(
                        "Area %s: Vacation mode active - using preset %s",
                        area_id, vacation_preset
                    )
                    if hasattr(self, 'area_logger') and self.area_logger:
                        self.area_logger.log_event(
                            area_id,
                            "mode",
                            f"Vacation mode active - preset set to {vacation_preset}",
                            {"preset_mode": vacation_preset, "vacation_mode": True}
                        )
            
            # Get effective target (considering schedules and night boost)
            target_temp = area.get_effective_target_temperature(current_time)
            _LOGGER.info(
                "Area %s: Effective target=%.1f°C (boost_active=%s, preset=%s, base_target=%.1f°C)",
                area_id, target_temp, area.boost_mode_active, area.preset_mode, area.target_temperature
            )
            if hasattr(self, 'area_logger') and self.area_logger:
                details = {
                    "target_temp": target_temp,
                    "boost_active": area.boost_mode_active,
                    "preset_mode": area.preset_mode,
                    "base_target": area.target_temperature
                }
                self.area_logger.log_event(
                    area_id,
                    "temperature",
                    f"Effective target temperature: {target_temp:.1f}°C",
                    details
                )
            
            # Apply frost protection if enabled (global setting)
            if self.area_manager.frost_protection_enabled:
                frost_temp = self.area_manager.frost_protection_temp
                if target_temp < frost_temp:
                    _LOGGER.debug(
                        "Area %s: Frost protection active - raising target from %.1f°C to %.1f°C",
                        area_id, target_temp, frost_temp
                    )
                    target_temp = frost_temp
            
            # Apply vacation mode frost protection override if active
            if vacation_manager and vacation_manager.is_active():
                vacation_min_temp = vacation_manager.get_min_temperature()
                if vacation_min_temp and target_temp < vacation_min_temp:
                    _LOGGER.debug(
                        "Area %s: Vacation frost protection - raising target from %.1f°C to %.1f°C",
                        area_id, target_temp, vacation_min_temp
                    )
                    target_temp = vacation_min_temp
            
            # Apply HVAC mode (off/heat/cool/auto)
            if hasattr(area, 'hvac_mode'):
                if area.hvac_mode == "off":
                    # HVAC mode is off - disable heating for this area
                    await self._async_set_area_heating(area, False)
                    area.state = "off"
                    _LOGGER.debug("Area %s: HVAC mode is OFF - skipping", area_id)
                    continue
            
            current_temp = area.current_temperature
            
            if current_temp is None:
                _LOGGER.warning("No temperature data for area %s", area_id)
                continue
            
            # Get hysteresis for this area (use area-specific or global)
            hysteresis = area.hysteresis_override if area.hysteresis_override is not None else self._hysteresis
            
            # Determine if heating is needed (with hysteresis)
            should_heat = current_temp < (target_temp - hysteresis)
            should_stop = current_temp >= target_temp
            
            # Log hysteresis decision for area logger
            if hasattr(self, 'area_logger') and self.area_logger:
                if not should_heat and current_temp < target_temp:
                    # Temperature is below target but within hysteresis band
                    self.area_logger.log_event(
                        area_id,
                        "climate_control",
                        f"Waiting for hysteresis ({hysteresis:.1f}°C) - not heating yet",
                        {
                            "current_temp": current_temp,
                            "target_temp": target_temp,
                            "hysteresis": hysteresis,
                            "threshold": target_temp - hysteresis,
                            "reason": "Within hysteresis band - prevents short cycling"
                        }
                    )
            
            if should_heat:
                # Start heating event if not already active and learning engine available
                if self.learning_engine and area_id not in self._area_heating_events:
                    outdoor_temp = await self._async_get_outdoor_temperature(area)
                    await self.learning_engine.async_start_heating_event(
                        area_id=area_id,
                        current_temp=current_temp,
                    )
                    _LOGGER.debug(
                        "Started learning event for area %s (outdoor: %s°C)",
                        area_id, outdoor_temp if outdoor_temp else "N/A"
                    )
                
                await self._async_set_area_heating(area, True, target_temp)
                area.state = "heating"  # Update area state
                heating_areas.append(area)
                max_target_temp = max(max_target_temp, target_temp)
                _LOGGER.info(
                    "Area %s: Heating ON (current: %.1f°C, target: %.1f°C)",
                    area_id, current_temp, target_temp
                )
                if hasattr(self, 'area_logger') and self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "heating",
                        f"Heating started - reaching {target_temp:.1f}°C",
                        {
                            "current_temp": current_temp,
                            "target_temp": target_temp,
                            "state": "heating"
                        }
                    )
            elif should_stop:
                # End heating event if active and learning engine available
                if self.learning_engine and area_id in self._area_heating_events:
                    del self._area_heating_events[area_id]
                    await self.learning_engine.async_end_heating_event(
                        area_id=area_id,
                        current_temp=current_temp,
                        target_reached=True
                    )
                    _LOGGER.debug(
                        "Completed learning event for area %s (reached %.1f°C)",
                        area_id, current_temp
                    )
                
                # Turn off heating but update target temperature to schedule value
                await self._async_set_area_heating(area, False, target_temp)
                area.state = "idle"  # Update area state
                _LOGGER.debug(
                    "Area %s: Heating OFF (current: %.1f°C, target: %.1f°C)",
                    area_id, current_temp, target_temp
                )
                if hasattr(self, 'area_logger') and self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "heating",
                        f"Heating stopped - target {target_temp:.1f}°C reached",
                        {
                            "current_temp": current_temp,
                            "target_temp": target_temp,
                            "state": "idle"
                        }
                    )
        
        # Control OpenTherm gateway (boiler) based on aggregated demand
        await self._async_control_opentherm_gateway(len(heating_areas) > 0, max_target_temp)
        
        # Save history periodically (every 5 minutes)
        if should_record_history and history_tracker:
            await history_tracker.async_save()

    async def _async_set_area_heating(
        self, area: Area, heating: bool, target_temp: float | None = None
    ) -> None:
        """Set heating state for an area.
        
        Controls all devices in the area:
        - Thermostats: Set temperature
        - Switches: Turn on/off (pumps, relays)
        - Valves/TRVs: Open/close or set temperature based on capabilities
        
        Args:
            area: Area instance
            heating: True to turn on heating, False to turn off
            target_temp: Target temperature
        """
        # Control thermostats
        await self._async_control_thermostats(area, heating, target_temp)
        
        # Control switches (pumps, relays)
        await self._async_control_switches(area, heating)
        
        # Control valves/TRVs
        await self._async_control_valves(area, heating, target_temp)

    async def _async_control_thermostats(
        self, area: Area, heating: bool, target_temp: float | None
    ) -> None:
        """Control thermostats in an area."""
        thermostats = area.get_thermostats()
        
        for thermostat_id in thermostats:
            try:
                if heating and target_temp is not None:
                    # Only set temperature if it has changed (to avoid API rate limiting)
                    last_temp = self._last_set_temperatures.get(thermostat_id)
                    if last_temp is None or abs(last_temp - target_temp) >= 0.1:
                        # Turn on and set temperature
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
                            "Skipping thermostat %s update - already at %.1f°C (avoiding API rate limit)",
                            thermostat_id, target_temp
                        )
                elif target_temp is not None:
                    # Only update target temperature if it has changed (to avoid API rate limiting)
                    last_temp = self._last_set_temperatures.get(thermostat_id)
                    if last_temp is None or abs(last_temp - target_temp) >= 0.1:
                        # Update target temperature even when not heating (for schedules)
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
                        _LOGGER.debug(
                            "Skipping thermostat %s update - already at %.1f°C (avoiding API rate limit)",
                            thermostat_id, target_temp
                        )
                else:
                    # Turn off heating completely (no target specified)
                    # Some devices (MQTT climate) don't support turn_off, so set to minimum temp instead
                    # Clear cached temperature when turning off
                    if thermostat_id in self._last_set_temperatures:
                        del self._last_set_temperatures[thermostat_id]
                    
                    # Try to turn off, but fall back to setting low temperature if not supported
                    try:
                        await self.hass.services.async_call(
                            CLIMATE_DOMAIN,
                            SERVICE_TURN_OFF,
                            {"entity_id": thermostat_id},
                            blocking=False,
                        )
                        _LOGGER.debug("Turned off thermostat %s", thermostat_id)
                    except Exception as turn_off_err:
                        # If turn_off not supported, set to frost protection or minimum temperature
                        min_temp = 5.0  # Frost protection minimum
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
                            "Thermostat %s doesn't support turn_off, set to %.1f°C instead",
                            thermostat_id, min_temp
                        )
            except Exception as err:
                _LOGGER.error(
                    "Failed to control thermostat %s: %s", 
                    thermostat_id, err
                )

    async def _async_control_switches(self, area: Area, heating: bool) -> None:
        """Control switches (pumps, relays) in an area."""
        switches = area.get_switches()
        
        for switch_id in switches:
            try:
                if heating:
                    # Turn on switch (pump, relay)
                    await self.hass.services.async_call(
                        "switch",
                        SERVICE_TURN_ON,
                        {"entity_id": switch_id},
                        blocking=False,
                    )
                    _LOGGER.debug("Turned on switch %s", switch_id)
                else:
                    # Turn off switch only if area setting allows it
                    if area.shutdown_switches_when_idle:
                        await self.hass.services.async_call(
                            "switch",
                            SERVICE_TURN_OFF,
                            {"entity_id": switch_id},
                            blocking=False,
                        )
                        _LOGGER.debug("Turned off switch %s (shutdown_switches_when_idle=True)", switch_id)
                    else:
                        _LOGGER.debug("Keeping switch %s on (shutdown_switches_when_idle=False)", switch_id)
            except Exception as err:
                _LOGGER.error(
                    "Failed to control switch %s: %s",
                    switch_id, err
                )

    async def _async_control_valves(
        self, area: Area, heating: bool, target_temp: float | None
    ) -> None:
        """Control valves/TRVs in an area.
        
        Dynamically detects valve capabilities and uses appropriate control method:
        - Position control: Direct 0-100% control via number.* entities or position attribute
        - Temperature control: High/low temp method for TRVs without position control
        
        Args:
            area: Area instance
            heating: True if area needs heating
            target_temp: Target temperature for the area
        """
        valves = area.get_valves()
        
        for valve_id in valves:
            try:
                # Query device capabilities dynamically
                capabilities = self._get_valve_capability(valve_id)
                
                # Prefer position control if available
                if capabilities['supports_position']:
                    domain = capabilities['entity_domain']
                    
                    if domain == 'number':
                        # Direct position control via number entity
                        if heating:
                            # Open valve to max
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
                                "Opened valve %s to %.0f%% (position control)",
                                valve_id, capabilities['position_max']
                            )
                        else:
                            # Close valve to min
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
                                "Closed valve %s to %.0f%% (position control)",
                                valve_id, capabilities['position_min']
                            )
                    
                    elif domain == 'climate' and 'position' in self.hass.states.get(valve_id).attributes:
                        # Climate entity with position attribute
                        # Try to set position via service
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
                            _LOGGER.debug(
                                "Set valve %s position to %.0f%%",
                                valve_id, position
                            )
                        except Exception:
                            # Fall back to temperature control if position service doesn't exist
                            _LOGGER.debug(
                                "Valve %s doesn't support set_position service, using temperature control",
                                valve_id
                            )
                            capabilities['supports_position'] = False
                            capabilities['supports_temperature'] = True
                
                # Fall back to temperature control if position not supported
                if not capabilities['supports_position'] and capabilities['supports_temperature']:
                    # TRV with temperature control only
                    # Use high/low temperature method
                    if heating and target_temp is not None:
                        # Set to heating temperature using configured offset
                        # Use actual target + offset to ensure valve opens
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
                            "Set TRV %s to heating temp %.1f°C (target %.1f°C + %.1f°C offset)", 
                            valve_id, heating_temp, target_temp, offset
                        )
                    else:
                        # Set to idle temperature (default 10°C or configured)
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
                            "Set TRV %s to idle temp %.1f°C (temperature control)", 
                            valve_id, idle_temp
                        )
                
                # If neither method is supported, log warning
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

    async def _async_get_outdoor_temperature(self, area: Area) -> float | None:
        """Get outdoor temperature for learning.
        
        Args:
            area: Area instance (checks weather_entity_id)
            
        Returns:
            Outdoor temperature or None if not available
        """
        if not area.weather_entity_id:
            return None
        
        state = self.hass.states.get(area.weather_entity_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        
        try:
            temp = float(state.state)
            # Check for Fahrenheit and convert
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp = (temp - 32) * 5/9
            return temp
        except (ValueError, TypeError):
            return None

    async def _async_control_opentherm_gateway(
        self, any_heating: bool, max_target_temp: float
    ) -> None:
        """Control the global OpenTherm gateway based on aggregated area demands.
        
        Args:
            any_heating: True if any area needs heating
            max_target_temp: Highest requested temperature across all heating areas
        """
        if not self.area_manager.opentherm_enabled:
            return
        
        gateway_id = self.area_manager.opentherm_gateway_id
        if not gateway_id:
            return
        
        try:
            if any_heating:
                # At least one area needs heating - turn on boiler
                # Set to highest requested temperature plus overhead
                boiler_setpoint = max_target_temp + 20  # Add 20°C for distribution losses
                
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
                    "OpenTherm gateway: Boiler ON, setpoint=%.1f°C (max area target=%.1f°C)",
                    boiler_setpoint, max_target_temp
                )
            else:
                # No areas need heating - turn off boiler
                await self.hass.services.async_call(
                    CLIMATE_DOMAIN,
                    SERVICE_TURN_OFF,
                    {"entity_id": gateway_id},
                    blocking=False,
                )
                _LOGGER.info("OpenTherm gateway: Boiler OFF (no heating demand)")
                
        except Exception as err:
            _LOGGER.error(
                "Failed to control OpenTherm gateway %s: %s",
                gateway_id, err
            )
