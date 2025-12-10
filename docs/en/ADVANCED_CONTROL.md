# Advanced Boiler Control (Heating Curve, PWM, PID, OPV)

This document explains the new optional Advanced Control features added to Smart Heating. These features are disabled by default and must be enabled in Global Settings.

## Features

- Heating Curve: Calculate boiler flow temperature from target room temperature and outside temperature using a configurable coefficient. Supports different formulas for radiator vs. underfloor heating.
- PID Controller: Optional PID loop that can be enabled and used to fine-tune boiler control with automatic gains.
- PWM (Pulse Width Modulation): For boilers that don't support modulation, approximate modulation using ON/OFF cycles with a duty cycle.
- Overshoot Protection (OPV): An OPV calibration routine that calculates a control value to prevent low-load overshoot.
- Per-Area settings: Each area can be configured with a `heating_type` (radiator or floor_heating) and an optional `heating_curve_coefficient`.

## Flow Temperature Defaults & Recommendations

- The integration now ships with updated practical defaults for flow temperatures depending on the heating system type.
  - Underfloor / floor heating: default baseline flow temperature is set to 40°C. This is in the typical range of 35-45°C used for most underfloor installations and should warm rooms faster than the previous very-low defaults.
  - Radiator systems: default baseline flow temperature is set to 55°C. Radiators typically require higher supply temperatures (50-70°C) depending on radiator size and system design.

If you find your system takes too long to reach the target room temperature, set your area `heating_type` correctly and consider tuning the `heating_curve_coefficient` or specifying per-device minimum flow temperatures in the Global Settings or per-area configuration.

## Safety

- Calibration should only be run with an OpenTherm Gateway that supports the commands and in a controlled environment. Calibration pauses normal control for a short period.

## How it works

- The integration computes a per-area heating curve based on the configured coefficient and the outside temperature sensor (if configured).
- If PID is enabled, the PID output is applied to the setpoint to reduce deviation between room temperature and target.
- When PWM is enabled and the gateway does not support modulation, a simple duty-cycle approximation is used to reduce boiler cycling.

## Configuration

- Global Settings > Advanced Control contains toggles to enable advanced control, heating curve, PID, PWM, and OPV.
- Default coefficients and default consumption/power values can be set in Global Settings.
- Areas define `heating_type` and optional `heating_curve_coefficient` per area.

## Implementation and API

- REST endpoints:
  - `GET /api/smart_heating/config` : configuration includes advanced control fields
  - `POST /api/smart_heating/config/advanced_control` : configure advanced control
  - `POST /api/smart_heating/opentherm/calibrate` : trigger OPV calibration (returns `opv` value)

## Notes for Developers

- Key modules:
  - `smart_heating/heating_curve.py`
  - `smart_heating/pid.py`
  - `smart_heating/pwm.py`
  - `smart_heating/overshoot_protection.py`
  - `smart_heating/minimum_setpoint.py`
  - `smart_heating/flame.py`
  - `smart_heating/sensor.py` (new per-area sensors)

- Ensure that advanced features are only enabled/used when `area_manager.advanced_control_enabled` is True.
