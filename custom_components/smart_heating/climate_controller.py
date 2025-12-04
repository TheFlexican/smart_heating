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

from .area_manager import AreaManager, Area
from .const import (
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
)

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control heating based on area settings and schedules."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager) -> None:
        """Initialize the climate controller.
        
        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
        """
        self.hass = hass
        self.area_manager = area_manager
        self._hysteresis = 0.5  # Temperature hysteresis in °C
        self._record_counter = 0  # Counter for history recording

    async def async_update_area_temperatures(self) -> None:
        """Update current temperatures for all areas from sensors."""
        for area_id, area in self.area_manager.get_all_areas().items():
            # Get temperature sensors for this area
            temp_sensors = area.get_temperature_sensors()
            
            if not temp_sensors:
                continue
            
            # Calculate average temperature from all sensors
            temps = []
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
            
            if temps:
                avg_temp = sum(temps) / len(temps)
                area.current_temperature = avg_temp
                _LOGGER.debug(
                    "Area %s temperature: %.1f°C (from %d sensors)",
                    area_id, avg_temp, len(temps)
                )

    async def async_control_heating(self) -> None:
        """Control heating for all areas based on temperature and schedules."""
        from .const import DOMAIN
        
        current_time = datetime.now()
        
        # First update all temperatures
        await self.async_update_area_temperatures()
        
        # Increment counter for history recording (every 10 cycles = 5 minutes)
        self._record_counter += 1
        should_record_history = (self._record_counter % 10 == 0)
        
        # Get history tracker if available
        history_tracker = self.hass.data.get(DOMAIN, {}).get("history")
        
        # Then control each area
        for area_id, area in self.area_manager.get_all_areas().items():
            if not area.enabled:
                # Area disabled - turn off heating
                await self._async_set_area_heating(area, False)
                area.state = "off"  # Update area state
                continue
            
            # Get effective target (considering schedules and night boost)
            target_temp = area.get_effective_target_temperature(current_time)
            current_temp = area.current_temperature
            
            if current_temp is None:
                _LOGGER.warning("No temperature data for area %s", area_id)
                continue
            
            # Record history (every 5 minutes)
            if should_record_history and history_tracker:
                await history_tracker.async_record_temperature(
                    area_id, current_temp, target_temp, area.state
                )
            
            # Determine if heating is needed (with hysteresis)
            should_heat = current_temp < (target_temp - self._hysteresis)
            should_stop = current_temp >= target_temp
            
            if should_heat:
                await self._async_set_area_heating(area, True, target_temp)
                area.state = "heating"  # Update area state
                _LOGGER.info(
                    "Area %s: Heating ON (current: %.1f°C, target: %.1f°C)",
                    area_id, current_temp, target_temp
                )
            elif should_stop:
                # Turn off heating but update target temperature to schedule value
                await self._async_set_area_heating(area, False, target_temp)
                area.state = "idle"  # Update area state
                _LOGGER.debug(
                    "Area %s: Heating OFF (current: %.1f°C, target: %.1f°C)",
                    area_id, current_temp, target_temp
                )
        
        # Save history periodically (every 5 minutes)
        if should_record_history and history_tracker:
            await history_tracker.async_save()

    async def _async_set_area_heating(
        self, area: Area, heating: bool, target_temp: float | None = None
    ) -> None:
        """Set heating state for an area.
        
        Args:
            area: Area instance
            heating: True to turn on heating, False to turn off
            target_temp: Target temperature (only used when heating=True)
        """
        thermostats = area.get_thermostats()
        
        for thermostat_id in thermostats:
            try:
                if heating and target_temp is not None:
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
                    _LOGGER.debug(
                        "Set %s to %.1f°C", thermostat_id, target_temp
                    )
                elif target_temp is not None:
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
                    _LOGGER.debug(
                        "Updated %s target to %.1f°C (idle)", thermostat_id, target_temp
                    )
                else:
                    # Turn off heating completely (no target specified)
                    await self.hass.services.async_call(
                        CLIMATE_DOMAIN,
                        SERVICE_TURN_OFF,
                        {"entity_id": thermostat_id},
                        blocking=False,
                    )
                    _LOGGER.debug("Turned off %s", thermostat_id)
            except Exception as err:
                _LOGGER.error(
                    "Failed to control thermostat %s: %s", 
                    thermostat_id, err
                )
