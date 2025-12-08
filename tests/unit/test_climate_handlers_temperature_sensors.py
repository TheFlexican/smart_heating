"""Tests for climate_handlers.temperature_sensors module."""
from unittest.mock import MagicMock

import pytest

from smart_heating.climate_handlers.temperature_sensors import TemperatureSensorHandler
from smart_heating.models import Area


class MockHomeAssistant:
    """Mock Home Assistant instance."""
    
    def __init__(self):
        """Initialize mock."""
        self.states = MagicMock()


@pytest.fixture
def mock_hass():
    """Return mocked Home Assistant instance."""
    return MockHomeAssistant()


@pytest.fixture
def mock_area():
    """Return mocked area."""
    area = MagicMock(spec=Area)
    area.get_temperature_sensors = MagicMock(return_value=[])
    area.get_thermostats = MagicMock(return_value=[])
    area.weather_entity_id = None
    return area


@pytest.fixture
def temp_handler(mock_hass):
    """Return TemperatureSensorHandler instance."""
    return TemperatureSensorHandler(hass=mock_hass)


class TestTemperatureSensorHandlerInit:
    """Test TemperatureSensorHandler initialization."""
    
    def test_init(self, mock_hass):
        """Test initialization."""
        handler = TemperatureSensorHandler(hass=mock_hass)
        
        assert handler.hass == mock_hass


class TestConvertFahrenheitToCelsius:
    """Test convert_fahrenheit_to_celsius method."""
    
    def test_freezing_point(self, temp_handler):
        """Test converting freezing point."""
        result = temp_handler.convert_fahrenheit_to_celsius(32.0)
        assert result == 0.0
    
    def test_room_temperature(self, temp_handler):
        """Test converting room temperature."""
        result = temp_handler.convert_fahrenheit_to_celsius(68.0)
        assert abs(result - 20.0) < 0.01
    
    def test_boiling_point(self, temp_handler):
        """Test converting boiling point."""
        result = temp_handler.convert_fahrenheit_to_celsius(212.0)
        assert result == 100.0


class TestGetTemperatureFromSensor:
    """Test get_temperature_from_sensor method."""
    
    def test_valid_celsius_temperature(self, temp_handler, mock_hass):
        """Test getting valid temperature in Celsius."""
        state = MagicMock()
        state.state = "21.5"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.temp1")
        
        assert result == 21.5
    
    def test_valid_fahrenheit_temperature(self, temp_handler, mock_hass):
        """Test getting valid temperature in Fahrenheit."""
        state = MagicMock()
        state.state = "70"
        state.attributes = {"unit_of_measurement": "°F"}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.temp_f")
        
        # 70°F = 21.11°C
        assert abs(result - 21.11) < 0.01
    
    def test_fahrenheit_alternative_unit(self, temp_handler, mock_hass):
        """Test Fahrenheit with 'F' unit (without degree symbol)."""
        state = MagicMock()
        state.state = "68"
        state.attributes = {"unit_of_measurement": "F"}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.temp_f2")
        
        # 68°F = 20°C
        assert abs(result - 20.0) < 0.01
    
    def test_sensor_unavailable(self, temp_handler, mock_hass):
        """Test sensor with unavailable state."""
        state = MagicMock()
        state.state = "unavailable"
        state.attributes = {}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.unavail")
        
        assert result is None
    
    def test_sensor_unknown(self, temp_handler, mock_hass):
        """Test sensor with unknown state."""
        state = MagicMock()
        state.state = "unknown"
        state.attributes = {}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.unknown")
        
        assert result is None
    
    def test_sensor_not_found(self, temp_handler, mock_hass):
        """Test sensor that doesn't exist."""
        mock_hass.states.get.return_value = None
        
        result = temp_handler.get_temperature_from_sensor("sensor.missing")
        
        assert result is None
    
    def test_invalid_temperature_value(self, temp_handler, mock_hass):
        """Test sensor with invalid temperature value."""
        state = MagicMock()
        state.state = "not_a_number"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_sensor("sensor.broken")
        
        assert result is None


class TestGetTemperatureFromThermostat:
    """Test get_temperature_from_thermostat method."""
    
    def test_valid_celsius_temperature(self, temp_handler, mock_hass):
        """Test getting valid temperature from thermostat in Celsius."""
        state = MagicMock()
        state.state = "heat"
        state.attributes = {
            "current_temperature": 20.5,
            "unit_of_measurement": "°C"
        }
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_thermostat("climate.thermo1")
        
        assert result == 20.5
    
    def test_valid_fahrenheit_temperature(self, temp_handler, mock_hass):
        """Test getting valid temperature from thermostat in Fahrenheit."""
        state = MagicMock()
        state.state = "heat"
        state.attributes = {
            "current_temperature": 68.0,
            "unit_of_measurement": "°F"
        }
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_thermostat("climate.thermo_f")
        
        # 68°F = 20°C
        assert abs(result - 20.0) < 0.01
    
    def test_thermostat_unavailable(self, temp_handler, mock_hass):
        """Test thermostat with unavailable state."""
        state = MagicMock()
        state.state = "unavailable"
        state.attributes = {}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_thermostat("climate.unavail")
        
        assert result is None
    
    def test_thermostat_not_found(self, temp_handler, mock_hass):
        """Test thermostat that doesn't exist."""
        mock_hass.states.get.return_value = None
        
        result = temp_handler.get_temperature_from_thermostat("climate.missing")
        
        assert result is None
    
    def test_no_current_temperature_attribute(self, temp_handler, mock_hass):
        """Test thermostat without current_temperature attribute."""
        state = MagicMock()
        state.state = "heat"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_thermostat("climate.no_temp")
        
        assert result is None
    
    def test_invalid_current_temperature(self, temp_handler, mock_hass):
        """Test thermostat with invalid current_temperature value."""
        state = MagicMock()
        state.state = "heat"
        state.attributes = {
            "current_temperature": "broken",
            "unit_of_measurement": "°C"
        }
        mock_hass.states.get.return_value = state
        
        result = temp_handler.get_temperature_from_thermostat("climate.broken")
        
        assert result is None


class TestCollectAreaTemperatures:
    """Test collect_area_temperatures method."""
    
    def test_no_sensors_or_thermostats(self, temp_handler, mock_area):
        """Test collecting temperatures with no sensors."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = []
        
        result = temp_handler.collect_area_temperatures(mock_area)
        
        assert result == []
    
    def test_only_temperature_sensors(self, temp_handler, mock_hass, mock_area):
        """Test collecting temperatures from temperature sensors only."""
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1", "sensor.temp2"]
        mock_area.get_thermostats.return_value = []
        
        state1 = MagicMock()
        state1.state = "20.5"
        state1.attributes = {"unit_of_measurement": "°C"}
        
        state2 = MagicMock()
        state2.state = "21.0"
        state2.attributes = {"unit_of_measurement": "°C"}
        
        mock_hass.states.get.side_effect = [state1, state2]
        
        result = temp_handler.collect_area_temperatures(mock_area)
        
        assert len(result) == 2
        assert 20.5 in result
        assert 21.0 in result
    
    def test_only_thermostats(self, temp_handler, mock_hass, mock_area):
        """Test collecting temperatures from thermostats only."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        
        state = MagicMock()
        state.state = "heat"
        state.attributes = {
            "current_temperature": 19.5,
            "unit_of_measurement": "°C"
        }
        mock_hass.states.get.return_value = state
        
        result = temp_handler.collect_area_temperatures(mock_area)
        
        assert result == [19.5]
    
    def test_mixed_sensors_and_thermostats(self, temp_handler, mock_hass, mock_area):
        """Test collecting temperatures from both sensors and thermostats."""
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1"]
        mock_area.get_thermostats.return_value = ["climate.thermo1"]
        
        sensor_state = MagicMock()
        sensor_state.state = "20.0"
        sensor_state.attributes = {"unit_of_measurement": "°C"}
        
        thermo_state = MagicMock()
        thermo_state.state = "heat"
        thermo_state.attributes = {
            "current_temperature": 20.5,
            "unit_of_measurement": "°C"
        }
        
        mock_hass.states.get.side_effect = [sensor_state, thermo_state]
        
        result = temp_handler.collect_area_temperatures(mock_area)
        
        assert len(result) == 2
        assert 20.0 in result
        assert 20.5 in result
    
    def test_skip_unavailable_sensors(self, temp_handler, mock_hass, mock_area):
        """Test that unavailable sensors are skipped."""
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1", "sensor.unavail"]
        mock_area.get_thermostats.return_value = []
        
        state1 = MagicMock()
        state1.state = "20.0"
        state1.attributes = {"unit_of_measurement": "°C"}
        
        state2 = MagicMock()
        state2.state = "unavailable"
        state2.attributes = {}
        
        mock_hass.states.get.side_effect = [state1, state2]
        
        result = temp_handler.collect_area_temperatures(mock_area)
        
        assert result == [20.0]


class TestAsyncGetOutdoorTemperature:
    """Test async_get_outdoor_temperature method."""
    
    @pytest.mark.asyncio
    async def test_no_weather_entity(self, temp_handler, mock_area):
        """Test when area has no weather entity configured."""
        mock_area.weather_entity_id = None
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_valid_celsius_temperature(self, temp_handler, mock_hass, mock_area):
        """Test getting valid outdoor temperature in Celsius."""
        mock_area.weather_entity_id = "weather.home"
        
        state = MagicMock()
        state.state = "5.5"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        assert result == 5.5
    
    @pytest.mark.asyncio
    async def test_valid_fahrenheit_temperature(self, temp_handler, mock_hass, mock_area):
        """Test getting valid outdoor temperature in Fahrenheit."""
        mock_area.weather_entity_id = "weather.home"
        
        state = MagicMock()
        state.state = "41"
        state.attributes = {"unit_of_measurement": "°F"}
        mock_hass.states.get.return_value = state
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        # 41°F = 5°C
        assert abs(result - 5.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_weather_unavailable(self, temp_handler, mock_hass, mock_area):
        """Test when weather entity is unavailable."""
        mock_area.weather_entity_id = "weather.home"
        
        state = MagicMock()
        state.state = "unavailable"
        state.attributes = {}
        mock_hass.states.get.return_value = state
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_weather_not_found(self, temp_handler, mock_hass, mock_area):
        """Test when weather entity doesn't exist."""
        mock_area.weather_entity_id = "weather.missing"
        mock_hass.states.get.return_value = None
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalid_temperature_value(self, temp_handler, mock_hass, mock_area):
        """Test when weather entity has invalid temperature."""
        mock_area.weather_entity_id = "weather.home"
        
        state = MagicMock()
        state.state = "not_a_number"
        state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get.return_value = state
        
        result = await temp_handler.async_get_outdoor_temperature(mock_area)
        
        assert result is None
