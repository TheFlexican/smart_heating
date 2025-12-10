from smart_heating.heating_curve import HeatingCurve
from smart_heating.pwm import PWM, CycleConfig


def test_pwm_duty_cycle_basic():
    hc = HeatingCurve(heating_system="radiator", coefficient=1.0)
    pwm = PWM(cycles=CycleConfig(), heating_curve=hc)
    pwm.enable()
    pwm.update(60.0, 50.0)
    assert pwm.duty_cycle is not None
