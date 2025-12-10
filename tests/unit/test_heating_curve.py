import pytest
from smart_heating.heating_curve import (
    HEATING_SYSTEM_RADIATOR,
    HEATING_SYSTEM_UNDERFLOOR,
    HeatingCurve,
)


def test_calculate_base_values():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    val = hc.calculate(20, 10)  # target 20, outside 10
    assert isinstance(val, float)


def test_update_and_value():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR, coefficient=1.2)
    hc.update(21.0, 5.0)
    assert hc.value is not None


def test_calculate_coefficient():
    hc = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    coeff = hc.calculate_coefficient(
        setpoint=55.0, target_temperature=20.0, outside_temperature=0.0
    )
    assert isinstance(coeff, float)


def test_default_base_offsets():
    hc_floor = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR, coefficient=1.0)
    hc_rad = HeatingCurve(heating_system=HEATING_SYSTEM_RADIATOR, coefficient=1.0)
    assert hc_floor.base_offset == pytest.approx(40.0, rel=1e-3)
    assert hc_rad.base_offset == pytest.approx(55.0, rel=1e-3)
