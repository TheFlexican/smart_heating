"""Heating curve controller modeled after SAT (Smart Autotune Thermostat).

Provides a HeatingCurve class that calculates base offset and recommended flow temperature
based on outdoor temperature and area target temperature. Also supports coefficient tuning
and a basic autotune heuristic.

This module is optional and enabled by global feature flag in configuration.
"""

from __future__ import annotations

from collections import deque
from statistics import mean
from typing import Optional

MINIMUM_SETPOINT = 10.0

# Heating system types
HEATING_SYSTEM_UNDERFLOOR = "underfloor"
HEATING_SYSTEM_RADIATOR = "radiator"


class HeatingCurve:
    """HeatingCurve calculates a recommended boiler flow temperature from
    target room setpoint and outdoor temperature.

    simple interface inspired by SAT:
        - calculate(target_temperature, outside_temperature): core function
        - calculate_coefficient: convert setpoint to coefficient
        - autotune: adaptive coefficient adjustment using fuzzy heuristics
        - base_offset: 20 for underfloor, 27.2 for radiators by default
    """

    def __init__(
        self, heating_system: str = HEATING_SYSTEM_RADIATOR, coefficient: float = 1.0
    ):
        self._heating_system = heating_system
        self._coefficient = coefficient
        self.reset()

    def reset(self) -> None:
        self._optimal_coefficient: Optional[float] = None
        self._coefficient_derivative: Optional[float] = None
        self._last_heating_curve_value: Optional[float] = None
        self._optimal_coefficients = deque(maxlen=5)

    def update(self, target_temperature: float, outside_temperature: float) -> None:
        heating_curve_value = self.calculate(target_temperature, outside_temperature)
        self._last_heating_curve_value = round(
            self.base_offset + ((self._coefficient / 4) * heating_curve_value), 1
        )

    def calculate_coefficient(
        self, setpoint: float, target_temperature: float, outside_temperature: float
    ) -> float:
        heating_curve_value = self.calculate(target_temperature, outside_temperature)
        if heating_curve_value == 0:
            return self._coefficient
        return round(4 * (setpoint - self.base_offset) / heating_curve_value, 1)

    def autotune(
        self, setpoint: float, target_temperature: float, outside_temperature: float
    ) -> Optional[float]:
        """Autotune heuristic: compute a coefficient from current setpoint and adjust
        using small fuzzy rules before storing an average value. Returns the computed coefficient."""
        if setpoint <= MINIMUM_SETPOINT:
            return None

        coefficient = self.calculate_coefficient(
            setpoint, target_temperature, outside_temperature
        )
        if self._optimal_coefficient:
            self._coefficient_derivative = round(
                coefficient - self._optimal_coefficient, 1
            )
        else:
            self._coefficient_derivative = 0

        if self._coefficient_derivative > 1:
            coefficient -= 0.3
        elif self._coefficient_derivative < 0.5:
            coefficient -= 0.1
        elif self._coefficient_derivative < 1:
            coefficient -= 0.2

        if self._coefficient_derivative < -1:
            coefficient += 0.3
        elif self._coefficient_derivative > -0.5:
            coefficient += 0.1
        elif self._coefficient_derivative > -1:
            coefficient += 0.2

        self._optimal_coefficients.append(coefficient)
        self._optimal_coefficient = round(mean(self._optimal_coefficients), 1)
        return self._optimal_coefficient

    def restore_autotune(self, coefficient: float, derivative: float):
        self._optimal_coefficient = coefficient
        self._coefficient_derivative = derivative
        self._optimal_coefficients = deque([coefficient] * 5, maxlen=5)

    @staticmethod
    def calculate(target_temperature: float, outside_temperature: float) -> float:
        """Default heating curve function. Uses a simple quadratic tweak similar to SAT's version.

        This formula is intentionally unconstrained and is configurable via coefficient.
        """
        # A small formula that models curve based on outside temp difference
        return (
            4 * (target_temperature - 20)
            + 0.03 * (outside_temperature - 20) ** 2
            - 0.4 * (outside_temperature - 20)
        )

    @property
    def base_offset(self) -> float:
        # Use more realistic baseline flow temperatures per system type
        # Underfloor systems typically use lower flow temperatures than radiators,
        # but the app and device show target setpoints that were too low for
        # effective heating; set defaults to practical ranges.
        # - underfloor: ~40°C typical flow temperature
        # - radiator: ~55°C typical flow temperature
        return 40.0 if self._heating_system == HEATING_SYSTEM_UNDERFLOOR else 55.0

    @property
    def optimal_coefficient(self) -> Optional[float]:
        return self._optimal_coefficient

    @property
    def coefficient_derivative(self) -> Optional[float]:
        return self._coefficient_derivative

    @property
    def value(self) -> Optional[float]:
        return self._last_heating_curve_value
