import pytest
from smart_heating.minimum_setpoint import MinimumSetpoint


def test_minimum_setpoint_initial_value():
    ms = MinimumSetpoint(configured_minimum_setpoint=40.0)
    assert ms.current_minimum_setpoint == pytest.approx(40.0, rel=1e-3)


def test_minimum_setpoint_update_with_return_temp():
    ms = MinimumSetpoint(configured_minimum_setpoint=40.0)
    boiler_state = type("_b", (), {})()
    boiler_state.return_temperature = 44.0
    boiler_state.flow_temperature = 40.0
    ms.calculate(boiler_state)
    # return_temp > flow_temp - 5: difference = 44 - (40 - 5) = 9
    # adjustment = difference * (adjustment_factor / 5.0) = 9 * 0.2 = 1.8
    assert ms.current_minimum_setpoint == pytest.approx(41.8, rel=1e-3)
