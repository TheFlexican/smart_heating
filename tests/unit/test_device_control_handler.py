from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from smart_heating.climate_handlers.device_control import DeviceControlHandler
from smart_heating.models.area import Area


def make_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


def make_area():
    area = MagicMock(spec=Area)
    area.get_thermostats.return_value = []
    area.get_switches.return_value = []
    area.get_valves.return_value = []
    area.area_id = "a1"
    return area


def test_is_any_thermostat_actively_heating_and_cooling():
    hass = make_hass()
    am = MagicMock()
    handler = DeviceControlHandler(hass, am)
    area = make_area()
    area.get_thermostats.return_value = ["climate.therm1", "climate.therm2"]

    # heating present
    state = MagicMock()
    state.attributes = {"hvac_action": "heating"}
    hass.states.get = MagicMock(return_value=state)
    assert handler.is_any_thermostat_actively_heating(area)
    assert not handler.is_any_thermostat_actively_cooling(area)

    # cooling present
    state.attributes = {"hvac_action": "cooling"}
    hass.states.get = MagicMock(return_value=state)
    assert not handler.is_any_thermostat_actively_heating(area)
    assert handler.is_any_thermostat_actively_cooling(area)


def test_get_valve_capability_number_and_climate_domains():
    hass = make_hass()
    am = MagicMock()
    handler = DeviceControlHandler(hass, am)

    # number domain
    number_state = MagicMock()
    number_state.attributes = {"min": 10, "max": 80}
    hass.states.get = MagicMock(return_value=number_state)
    res = handler.get_valve_capability("number.valve1")
    assert res["supports_position"] is True
    assert res["position_min"] == 10
    assert res["position_max"] == 80

    # climate with position attribute
    climate_state = MagicMock()
    climate_state.attributes = {"position": 40, "temperature": 25}
    hass.states.get = MagicMock(return_value=climate_state)
    res2 = handler.get_valve_capability("climate.valve2")
    assert res2["supports_position"] is True
    assert res2["supports_temperature"] is True

    # missing entity -> default capabilities
    hass.states.get = MagicMock(return_value=None)
    res3 = handler.get_valve_capability("number.missing")
    assert res3["supports_position"] is False


def test_parse_hysteresis_variants():
    hass = make_hass()
    am = MagicMock()
    am.hysteresis = 1.2
    handler = DeviceControlHandler(hass, am)
    area = make_area()

    area.hysteresis_override = 0.8
    assert abs(handler._parse_hysteresis(area) - 0.8) < 1e-6

    area.hysteresis_override = "1.5"
    assert abs(handler._parse_hysteresis(area) - 1.5) < 1e-6

    area.hysteresis_override = MagicMock()
    assert abs(handler._parse_hysteresis(area) - 1.2) < 1e-6

    am.hysteresis = "2"
    area.hysteresis_override = None
    assert abs(handler._parse_hysteresis(area) - 2.0) < 1e-6

    am.hysteresis = None
    assert abs(handler._parse_hysteresis(area) - 0.5) < 1e-6


@pytest.mark.asyncio
async def test_handle_thermostat_idle_sets_to_current_or_target():
    hass = make_hass()
    am = MagicMock()
    handler = DeviceControlHandler(hass, am)
    area = make_area()
    area.hysteresis_override = 1.0
    area.current_temperature = 22.0
    # thermostat id
    tid = "climate.t1"
    # last set temp None
    handler._last_set_temperatures = {}
    await handler._handle_thermostat_idle(area, tid, 21.0)
    # Since current >= (target - hyst) desired_setpoint should be current temp (22.0)
    assert handler._last_set_temperatures[tid] == 22.0  # NOSONAR
    # Call again, should skip because last_temp equals desired
    hass.services.async_call.reset_mock()
    await handler._handle_thermostat_idle(area, tid, 21.0)
    hass.services.async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_thermostat_turn_off_behavior():
    hass = make_hass()
    am = MagicMock()
    am.frost_protection_enabled = True
    am.frost_protection_temp = 6.0
    handler = DeviceControlHandler(hass, am)
    # Thermostat supports turn_off
    state = MagicMock()
    state.attributes = {"supported_features": 128}
    hass.states.get = MagicMock(return_value=state)
    handler._async_turn_off_climate_power = AsyncMock()
    await handler._handle_thermostat_turn_off("climate.t1")
    hass.services.async_call.assert_awaited()
    handler._async_turn_off_climate_power.assert_awaited()

    # Thermostat does not support turn_off -> set min (frost_protection_temp)
    state.attributes = {"supported_features": 0}
    hass.states.get = MagicMock(return_value=state)
    handler._last_set_temperatures = {}
    hass.services.async_call.reset_mock()
    await handler._handle_thermostat_turn_off("climate.t1")
    hass.services.async_call.assert_awaited()


def test_compute_area_candidate_with_heating_curve_and_pid():
    hass = make_hass()
    am = MagicMock()
    # Create area
    area = make_area()
    area.target_temperature = 21.0
    area.weather_entity_id = "weather.home"
    area.get_thermostats.return_value = []
    area.heating_curve_coefficient = None
    area.heating_type = "radiator"
    am.get_area.return_value = area
    # Set default heating curve coefficient
    am.default_heating_curve_coefficient = 1.0
    handler = DeviceControlHandler(hass, am)
    # configure weather state
    ws = MagicMock()
    ws.state = "10.0"
    ws.attributes = {"temperature": 10.0}
    hass.states.get = MagicMock(return_value=ws)

    # Compute candidate with heating curve enabled
    cand = handler._compute_area_candidate("a1", 0.0, True, True, False)
    assert isinstance(cand, float)

    # Now test PID path: assign a fake pid
    handler._pids["a1"] = MagicMock()
    handler._pids["a1"].update.return_value = 1.5
    area.current_temperature = 19.0
    # candidate before pid is target + overhead = 21.0
    cand2 = handler._compute_area_candidate("a1", 0.0, True, False, True)
    assert abs(cand2 - (21.0 + 1.5)) < 1e-6


@pytest.mark.asyncio
async def test_get_valve_capability_missing_entity():
    hass = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    handler = DeviceControlHandler(hass, MagicMock())
    cap = handler.get_valve_capability("valve.missing")
    assert cap["supports_position"] is False


@pytest.mark.asyncio
async def test_get_valve_capability_number_and_climate():
    hass = MagicMock()

    class MockState:
        def __init__(self, attrs):
            self.attributes = attrs
            self.entity_state = "on"

    # number domain
    hass.states.get = MagicMock(return_value=MockState({"min": 10, "max": 90}))
    handler = DeviceControlHandler(hass, MagicMock())
    cap = handler.get_valve_capability("number.valve1")
    assert cap["supports_position"] is True
    assert cap["position_min"] == 10

    # climate domain with position and temperature
    hass.states.get = MagicMock(return_value=MockState({"position": 50, "temperature": 21.0}))
    cap2 = handler.get_valve_capability("climate.trv1")
    assert cap2["supports_position"] is True
    assert cap2["supports_temperature"] is True


@pytest.mark.asyncio
async def test_async_ensure_and_turn_off_climate_power(monkeypatch):
    hass = MagicMock()
    handler = DeviceControlHandler(hass, MagicMock())

    # No dot in id
    await handler._async_ensure_climate_power_on("invalid")
    await handler._async_turn_off_climate_power("invalid")

    # With switch not on
    class MockState:
        def __init__(self, entity_state, attrs=None):
            self._state = entity_state
            self.attributes = attrs or {}

        @property
        def state(self):
            return self._state

    hass.states.get = MagicMock(return_value=MockState("off"))
    hass.services.async_call = AsyncMock()
    await handler._async_ensure_climate_power_on("climate.unit1")
    hass.services.async_call.assert_called()

    hass.states.get = MagicMock(return_value=MockState("on"))
    hass.services.async_call = AsyncMock()
    await handler._async_turn_off_climate_power("climate.unit1")
    hass.services.async_call.assert_called()


@pytest.mark.asyncio
async def test_handle_thermostat_heating_and_idle_and_turn_off():
    hass = MagicMock()
    handler = DeviceControlHandler(hass, MagicMock())

    # heating path: ensure services called and last set temp updated
    hass.states.get = MagicMock(return_value=MagicMock(attributes={}))
    hass.services.async_call = AsyncMock()
    await handler._handle_thermostat_heating("climate.t1", 21.5, "heat")
    assert handler._last_set_temperatures["climate.t1"] == 21.5  # NOSONAR

    # idle path: if current_temp >= target - hysteresis, should set to current temp
    area = MagicMock()
    area.hysteresis_override = 0.5
    area.current_temperature = 22.0
    handler._last_set_temperatures = {}
    hass.services.async_call = AsyncMock()
    await handler._handle_thermostat_idle(area, "climate.t1", 22.0)
    assert "climate.t1" in handler._last_set_temperatures

    # turn off supported
    state = MagicMock()
    state.attributes = {"supported_features": 128}
    hass.states.get = MagicMock(return_value=state)
    hass.services.async_call = AsyncMock()
    handler.area_manager = MagicMock()
    handler.area_manager.frost_protection_enabled = False
    await handler._handle_thermostat_turn_off("climate.t1")
    hass.services.async_call.assert_called()

    # turn off fallback
    state = MagicMock()
    state.attributes = {"supported_features": 0}
    hass.states.get = MagicMock(return_value=state)
    handler.area_manager = MagicMock()
    handler.area_manager.frost_protection_enabled = True
    handler.area_manager.frost_protection_temp = 6.0
    hass.services.async_call = AsyncMock()
    await handler._handle_thermostat_turn_off("climate.t2")
    hass.services.async_call.assert_called()


def test_collect_heating_areas_and_calculations():
    hass = MagicMock()
    area_manager = MagicMock()
    handler = DeviceControlHandler(hass, area_manager)

    area = MagicMock()
    area.state = "heating"
    area.heating_type = "radiator"
    area.current_temperature = 20.0
    area.target_temperature = 22.0
    area.name = "Zone"
    area.custom_overhead_temp = None

    area_manager.get_all_areas.return_value = {"a1": area}

    ot_logger = MagicMock()
    heating_ids, _, overheads = handler._collect_heating_areas(ot_logger)
    assert "a1" in heating_ids
    assert abs(overheads["a1"] - 20.0) < 0.001


def test_compute_candidate_and_enforce_minimum(monkeypatch):
    hass = MagicMock()
    area_manager = MagicMock()
    handler = DeviceControlHandler(hass, area_manager)

    # area missing
    area_manager.get_area.return_value = None
    assert handler._compute_area_candidate("nope", 2.0, False, False, False) is None

    # patch internal steps to control return values
    class Area:
        def __init__(self):
            self.target_temperature = 20.0
            self.weather_entity_id = "weather.home"
            self.heating_type = "radiator"

    a = Area()
    area_manager.get_area.return_value = a
    monkeypatch.setattr(handler, "_apply_heating_curve", lambda *a, **k: 25.0)
    monkeypatch.setattr(handler, "_apply_pid_adjustment", lambda *a, **k: 26.0)

    cand = handler._compute_area_candidate("a1", 2.0, True, True, True)
    assert cand == 26.0  # NOSONAR

    # enforce minimum
    a.heating_type = "floor_heating"
    area_manager.get_area.return_value = a
    handler.hass.states.get = MagicMock(
        return_value=MagicMock(attributes={"return_water_temp": 55.0, "ch_water_temp": 60.0})
    )
    boiler = handler._enforce_minimum_setpoints(["a1"], 30.0, "gateway.1")
    assert boiler >= 40.0


@pytest.mark.asyncio
async def test_async_control_switches_and_valves(monkeypatch):
    hass = MagicMock()
    area = MagicMock()
    area.get_switches.return_value = ["switch.1"]
    area.get_valves.return_value = ["number.trv1"]
    area.area_id = "a1"
    area.shutdown_switches_when_idle = True
    area.state = "idle"
    handler = DeviceControlHandler(hass, MagicMock())

    # is_any_thermostat_actively_heating returns True
    handler.is_any_thermostat_actively_heating = MagicMock(return_value=True)
    hass.services.async_call = AsyncMock()
    await handler.async_control_switches(area, False)
    hass.services.async_call.assert_called()

    # valves - number domain
    class MockState:
        def __init__(self, attrs):
            self.attributes = attrs
            self.entity_state = "on"

    hass.states.get = MagicMock(return_value=MockState({}))
    hass.services.async_call = AsyncMock()
    await handler.async_control_valves(area, True, 22.0)
    hass.services.async_call.assert_called()
