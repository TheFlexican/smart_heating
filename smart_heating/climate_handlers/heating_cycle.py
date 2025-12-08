"""Heating cycle management for climate control."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..models import Area

_LOGGER = logging.getLogger(__name__)


class HeatingCycleHandler:
    """Handle heating cycle logic and orchestration."""

    def __init__(
        self, hass: HomeAssistant, area_manager: AreaManager, learning_engine=None, area_logger=None
    ):
        """Initialize heating cycle handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            learning_engine: Optional learning engine
            area_logger: Optional area logger
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self.area_logger = area_logger
        self._area_heating_events = {}  # Track active heating events per area
        self._record_counter = 0

    async def async_prepare_heating_cycle(self, temp_handler, sensor_handler) -> tuple[bool, Any]:
        """Prepare for heating control cycle.

        Args:
            temp_handler: Temperature sensor handler
            sensor_handler: Sensor monitoring handler

        Returns:
            Tuple of (should_record_history, history_tracker)
        """
        from ..const import DOMAIN

        # Update all temperatures
        for area_id, area in self.area_manager.get_all_areas().items():
            temp_sensors = area.get_temperature_sensors()
            thermostats = area.get_thermostats()

            if not temp_sensors and not thermostats:
                continue

            temps = temp_handler.collect_area_temperatures(area)

            if temps:
                avg_temp = sum(temps) / len(temps)
                area.current_temperature = avg_temp
                _LOGGER.debug(
                    "Area %s temperature: %.1f°C (from %d sensors)", area_id, avg_temp, len(temps)
                )

        # Update window and presence sensor states
        await sensor_handler.async_update_sensor_states()

        # Check for expired boost modes
        for area in self.area_manager.get_all_areas().values():
            if area.boost_mode_active:
                area.check_boost_expiry()

        # Increment counter for history recording (every 10 cycles = 5 minutes)
        self._record_counter += 1
        should_record_history = self._record_counter % 10 == 0

        # Get history tracker if available
        history_tracker = self.hass.data.get(DOMAIN, {}).get("history")

        return should_record_history, history_tracker

    async def async_handle_heating_required(
        self,
        area_id: str,
        area: Area,
        current_temp: float,
        target_temp: float,
        device_handler,
        temp_handler,
    ) -> tuple[list, float]:
        """Handle when heating is required for an area.

        Returns:
            Tuple of (heating_areas list, max_target_temp)
        """
        heating_areas = [area]
        max_target_temp = target_temp

        # Start heating event if not already active
        if self.learning_engine and area_id not in self._area_heating_events:
            outdoor_temp = await temp_handler.async_get_outdoor_temperature(area)
            await self.learning_engine.async_start_heating_event(
                area_id=area_id,
                current_temp=current_temp,
            )
            self._area_heating_events[area_id] = True  # Track active heating event
            _LOGGER.debug(
                "Started learning event for area %s (outdoor: %s°C)",
                area_id,
                outdoor_temp if outdoor_temp else "N/A",
            )

        # Control all devices
        await device_handler.async_control_thermostats(area, True, target_temp)
        await device_handler.async_control_switches(area, True)
        await device_handler.async_control_valves(area, True, target_temp)

        area.state = "heating"
        _LOGGER.info(
            "Area %s: Heating ON (current: %.1f°C, target: %.1f°C)",
            area_id,
            current_temp,
            target_temp,
        )

        if self.area_logger:
            self.area_logger.log_event(
                area_id,
                "heating",
                f"Heating started - reaching {target_temp:.1f}°C",
                {"current_temp": current_temp, "target_temp": target_temp, "state": "heating"},
            )

        return heating_areas, max_target_temp

    async def async_handle_heating_stop(
        self, area_id: str, area: Area, current_temp: float, target_temp: float, device_handler
    ) -> None:
        """Handle when heating should stop for an area."""
        # Check if thermostats are still actively heating
        thermostats_still_heating = device_handler.is_any_thermostat_actively_heating(area)

        if thermostats_still_heating:
            _LOGGER.info(
                "Area %s: Target reached (%.1f°C/%.1f°C) but thermostat still heating - waiting for idle",
                area_id,
                current_temp,
                target_temp,
            )
            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "heating",
                    "Target reached but thermostat still heating - waiting for idle",
                    {
                        "current_temp": current_temp,
                        "target_temp": target_temp,
                        "state": "idle_pending",
                        "reason": "Thermostat hvac_action still reports heating",
                    },
                )

        # End heating event if active
        if self.learning_engine and area_id in self._area_heating_events:
            del self._area_heating_events[area_id]
            await self.learning_engine.async_end_heating_event(
                area_id=area_id, current_temp=current_temp
            )
            _LOGGER.debug(
                "Completed learning event for area %s (reached %.1f°C)", area_id, current_temp
            )

        # Turn off heating
        await device_handler.async_control_thermostats(area, False, target_temp)
        await device_handler.async_control_switches(area, False)
        await device_handler.async_control_valves(area, False, target_temp)

        area.state = "idle"
        _LOGGER.debug(
            "Area %s: Heating OFF (current: %.1f°C, target: %.1f°C)",
            area_id,
            current_temp,
            target_temp,
        )

        if self.area_logger and not thermostats_still_heating:
            self.area_logger.log_event(
                area_id,
                "heating",
                f"Heating stopped - target {target_temp:.1f}°C reached",
                {"current_temp": current_temp, "target_temp": target_temp, "state": "idle"},
            )

    async def async_handle_cooling_required(
        self,
        area_id: str,
        area: Area,
        current_temp: float,
        target_temp: float,
        device_handler,
        temp_handler,
    ) -> tuple[list, float]:
        """Handle when cooling is required for an area.

        Returns:
            Tuple of (cooling_areas list, min_target_temp)
        """
        cooling_areas = [area]
        min_target_temp = target_temp

        # Start cooling event if not already active
        if self.learning_engine and area_id not in self._area_heating_events:
            outdoor_temp = await temp_handler.async_get_outdoor_temperature(area)
            # Reuse heating event tracker for cooling events
            # TODO: Consider separate cooling event tracking in learning engine
            self._area_heating_events[area_id] = True  # Track active cooling event
            _LOGGER.debug(
                "Started cooling event for area %s (outdoor: %s°C)",
                area_id,
                outdoor_temp if outdoor_temp else "N/A",
            )

        # Control all devices in cooling mode
        await device_handler.async_control_thermostats(area, True, target_temp, hvac_mode="cool")
        await device_handler.async_control_switches(area, True)
        await device_handler.async_control_valves(area, True, target_temp)

        area.state = "cooling"
        _LOGGER.info(
            "Area %s: Cooling ON (current: %.1f°C, target: %.1f°C)",
            area_id,
            current_temp,
            target_temp,
        )

        if self.area_logger:
            self.area_logger.log_event(
                area_id,
                "cooling",
                f"Cooling started - reaching {target_temp:.1f}°C",
                {"current_temp": current_temp, "target_temp": target_temp, "state": "cooling"},
            )

        return cooling_areas, min_target_temp

    async def async_handle_cooling_stop(
        self, area_id: str, area: Area, current_temp: float, target_temp: float, device_handler
    ) -> None:
        """Handle when cooling should stop for an area."""
        # Check if thermostats are still actively cooling
        thermostats_still_cooling = device_handler.is_any_thermostat_actively_cooling(area)

        if thermostats_still_cooling:
            _LOGGER.info(
                "Area %s: Target reached (%.1f°C/%.1f°C) but thermostat still cooling - waiting for idle",
                area_id,
                current_temp,
                target_temp,
            )
            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "cooling",
                    "Target reached but thermostat still cooling - waiting for idle",
                    {
                        "current_temp": current_temp,
                        "target_temp": target_temp,
                        "state": "idle_pending",
                        "reason": "Thermostat hvac_action still reports cooling",
                    },
                )

        # End cooling event if active
        if self.learning_engine and area_id in self._area_heating_events:
            del self._area_heating_events[area_id]
            # TODO: Add async_end_cooling_event to learning engine
            _LOGGER.debug(
                "Completed cooling event for area %s (reached %.1f°C)", area_id, current_temp
            )

        # Turn off cooling
        await device_handler.async_control_thermostats(area, False, target_temp, hvac_mode="cool")
        await device_handler.async_control_switches(area, False)
        await device_handler.async_control_valves(area, False, target_temp)

        area.state = "idle"
        _LOGGER.debug(
            "Area %s: Cooling OFF (current: %.1f°C, target: %.1f°C)",
            area_id,
            current_temp,
            target_temp,
        )

        if self.area_logger and not thermostats_still_cooling:
            self.area_logger.log_event(
                area_id,
                "cooling",
                f"Cooling stopped - target {target_temp:.1f}°C reached",
                {"current_temp": current_temp, "target_temp": target_temp, "state": "idle"},
            )
