"""Temperature sensor handling for climate control."""
import logging
from typing import Optional

from homeassistant.core import HomeAssistant

from ..models import Area

_LOGGER = logging.getLogger(__name__)


class TemperatureSensorHandler:
    """Handle temperature sensor readings and conversions."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the temperature sensor handler.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    def convert_fahrenheit_to_celsius(self, temp_fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius.
        
        Args:
            temp_fahrenheit: Temperature in Fahrenheit
            
        Returns:
            Temperature in Celsius
        """
        return (temp_fahrenheit - 32) * 5/9

    def get_temperature_from_sensor(self, sensor_id: str) -> Optional[float]:
        """Get temperature from a sensor entity.
        
        Handles unit conversion (F to C) and invalid states.
        
        Args:
            sensor_id: Sensor entity ID
            
        Returns:
            Temperature in Celsius or None if unavailable
        """
        state = self.hass.states.get(sensor_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        
        try:
            temp_value = float(state.state)
            
            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = self.convert_fahrenheit_to_celsius(temp_value)
                _LOGGER.debug(
                    "Converted temperature from %s: %s°F -> %.1f°C",
                    sensor_id, state.state, temp_value
                )
            
            return temp_value
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid temperature from %s: %s", 
                sensor_id, state.state
            )
            return None

    def get_temperature_from_thermostat(self, thermostat_id: str) -> Optional[float]:
        """Get current temperature from a thermostat entity.
        
        Handles unit conversion (F to C) and invalid states.
        
        Args:
            thermostat_id: Thermostat entity ID
            
        Returns:
            Temperature in Celsius or None if unavailable
        """
        state = self.hass.states.get(thermostat_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        
        current_temp = state.attributes.get("current_temperature")
        if current_temp is None:
            return None
        
        try:
            temp_value = float(current_temp)
            
            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = self.convert_fahrenheit_to_celsius(temp_value)
                _LOGGER.debug(
                    "Converted temperature from thermostat %s: %.1f°F -> %.1f°C",
                    thermostat_id, current_temp, temp_value
                )
            
            return temp_value
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid current_temperature from thermostat %s: %s", 
                thermostat_id, current_temp
            )
            return None

    def collect_area_temperatures(self, area: Area) -> list[float]:
        """Collect all temperature readings for an area.
        
        Args:
            area: Area instance
            
        Returns:
            List of temperature values in Celsius
        """
        temps = []
        
        # Read from temperature sensors
        for sensor_id in area.get_temperature_sensors():
            temp = self.get_temperature_from_sensor(sensor_id)
            if temp is not None:
                temps.append(temp)
        
        # Read from thermostats
        for thermostat_id in area.get_thermostats():
            temp = self.get_temperature_from_thermostat(thermostat_id)
            if temp is not None:
                temps.append(temp)
        
        return temps

    async def async_get_outdoor_temperature(self, area: Area) -> Optional[float]:
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
