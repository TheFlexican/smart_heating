from smart_heating.heating_curve import HEATING_SYSTEM_UNDERFLOOR, MINIMUM_SETPOINT, HeatingCurve


def test_calculate_formula_and_base_offset():
    # Verify static calculate formula gives expected numeric behaviour
    val = HeatingCurve.calculate(22.0, 10.0)
    assert isinstance(val, float)

    # Check base_offset for systems
    hc_rad = HeatingCurve(heating_system="radiator")
    assert hc_rad.base_offset == 55.0  # NOSONAR
    hc_floor = HeatingCurve(heating_system=HEATING_SYSTEM_UNDERFLOOR)
    assert hc_floor.base_offset == 40.0  # NOSONAR


def test_calculate_coefficient_and_update():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    # if calculate returns zero, coefficient should remain unchanged
    # choose parameters so calculate == 0 approximately
    zero_val = hc.calculate(20.0, 20.0)
    assert abs(zero_val) < 1e-6
    coeff = hc.calculate_coefficient(
        setpoint=hc.base_offset, target_temperature=20.0, outside_temperature=20.0
    )
    assert coeff == hc._coefficient

    # update should set last value rounded (calls calculate internally)
    hc.update(22.0, 10.0)
    assert hc.value is not None


def test_autotune_behaviour_and_restore():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)

    # setpoint too low -> returns None
    assert hc.autotune(MINIMUM_SETPOINT, 22.0, 5.0) is None

    # normal autotune filling buffer and derivative adjustments
    # call multiple times with slightly different inputs to populate deque
    v1 = hc.autotune(50.0, 22.0, 10.0)
    assert isinstance(v1, float)
    v2 = hc.autotune(51.0, 22.0, 11.0)
    assert isinstance(v2, float)

    # test restore_autotune sets internal state
    hc.restore_autotune(1.5, 0.2)
    assert hc.optimal_coefficient == 1.5  # NOSONAR
    assert hc.coefficient_derivative == 0.2  # NOSONAR
