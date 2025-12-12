from unittest.mock import MagicMock

import pytest
from smart_heating.climate_handlers.temperature_sensors import TemperatureSensorHandler


def make_hass():
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


def test_convert_and_get_from_sensor_and_thermostat():
    hass = make_hass()
    handler = TemperatureSensorHandler(hass)

    # Fahrenheit sensor
    state = MagicMock()
    state.state = "68.0"
    state.attributes = {"unit_of_measurement": "°F"}
    hass.states.get = MagicMock(return_value=state)
    temp = handler.get_temperature_from_sensor("sensor.t1")
    assert temp == pytest.approx(20.0, abs=0.1)

    # invalid sensor
    state.state = "unavailable"
    hass.states.get = MagicMock(return_value=state)
    assert handler.get_temperature_from_sensor("sensor.t1") is None

    # thermostat current_temperature
    tstate = MagicMock()
    tstate.state = "heat"
    tstate.attributes = {"current_temperature": 21.0, "unit_of_measurement": "°C"}
    hass.states.get = MagicMock(return_value=tstate)
    assert handler.get_temperature_from_thermostat("climate.t1") == 21.0  # NOSONAR


def test_collect_area_temperatures_primary_and_fallback():
    hass = make_hass()
    handler = TemperatureSensorHandler(hass)
    area = MagicMock()
    area.area_id = "a1"
    area.primary_temperature_sensor = "sensor.primary"
    # Simulate primary sensor available
    s = MagicMock()
    s.state = "20.0"
    s.attributes = {"unit_of_measurement": "°C"}
    hass.states.get = MagicMock(return_value=s)
    temps = handler.collect_area_temperatures(area)
    assert temps == [20.0]

    # Primary not available -> fallback to sensors and thermostats
    area.primary_temperature_sensor = None
    area.get_temperature_sensors.return_value = ["sensor.s1"]
    area.get_thermostats.return_value = ["climate.t1"]
    s2 = MagicMock()
    s2.state = "21.5"
    s2.attributes = {"unit_of_measurement": "°C"}
    t = MagicMock()
    t.state = "heat"
    t.attributes = {"current_temperature": 20.0, "unit_of_measurement": "°C"}

    # hass.states.get must return appropriate for different IDs
    def get_state(entity_id):
        if entity_id.startswith("sensor"):
            return s2
        return t

    hass.states.get = MagicMock(side_effect=get_state)
    temps2 = handler.collect_area_temperatures(area)
    assert 21.5 in temps2
    assert 20.0 in temps2


@pytest.mark.asyncio
async def test_async_get_outdoor_temperature():
    hass = make_hass()
    handler = TemperatureSensorHandler(hass)
    area = MagicMock()
    area.weather_entity_id = "weather.home"
    state = MagicMock()
    state.state = "12.5"
    state.attributes = {"unit_of_measurement": "°C"}
    hass.states.get = MagicMock(return_value=state)
    t = await handler.async_get_outdoor_temperature(area)
    assert t == 12.5  # NOSONAR
