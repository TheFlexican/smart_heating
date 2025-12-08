"""Protection and override handlers for climate control."""

import logging

from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..models import Area

_LOGGER = logging.getLogger(__name__)


class ProtectionHandler:
    """Handle frost protection, vacation mode, and manual override."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager, area_logger=None):
        """Initialize protection handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            area_logger: Optional area logger for events
        """
        self.hass = hass
        self.area_manager = area_manager
        self.area_logger = area_logger

    def apply_frost_protection(self, area_id: str, target_temp: float) -> float:
        """Apply frost protection and vacation frost protection.

        Args:
            area_id: Area identifier
            target_temp: Current target temperature

        Returns:
            Adjusted target temperature with frost protection applied
        """
        # Apply global frost protection if enabled
        if self.area_manager.frost_protection_enabled:
            frost_temp = self.area_manager.frost_protection_temp
            if target_temp < frost_temp:
                _LOGGER.debug(
                    "Area %s: Frost protection active - raising target from %.1f°C to %.1f°C",
                    area_id,
                    target_temp,
                    frost_temp,
                )
                target_temp = frost_temp

        # Apply vacation mode frost protection override if active
        vacation_manager = self.hass.data.get("smart_heating", {}).get("vacation_manager")
        if vacation_manager and vacation_manager.is_active():
            vacation_min_temp = vacation_manager.get_min_temperature()
            if vacation_min_temp and target_temp < vacation_min_temp:
                _LOGGER.debug(
                    "Area %s: Vacation frost protection - raising target from %.1f°C to %.1f°C",
                    area_id,
                    target_temp,
                    vacation_min_temp,
                )
                target_temp = vacation_min_temp

        return target_temp

    def apply_vacation_mode(self, area_id: str, area: Area) -> None:
        """Apply vacation mode preset if active."""
        vacation_manager = self.hass.data.get("smart_heating", {}).get("vacation_manager")
        if vacation_manager and vacation_manager.is_active():
            vacation_preset = vacation_manager.get_preset_mode()
            if vacation_preset:
                area.preset_mode = vacation_preset
                _LOGGER.debug(
                    "Area %s: Vacation mode active - using preset %s", area_id, vacation_preset
                )
                if self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "mode",
                        f"Vacation mode active - preset set to {vacation_preset}",
                        {"preset_mode": vacation_preset, "vacation_mode": True},
                    )

    async def async_handle_manual_override(
        self, area_id: str, area: Area, device_control_handler
    ) -> None:
        """Handle manual override mode - log and control switches only.

        Args:
            area_id: Area identifier
            area: Area instance
            device_control_handler: Device control handler for switch control
        """
        _LOGGER.info("Area %s in MANUAL OVERRIDE mode - skipping thermostat control", area_id)
        area.state = "manual"
        if self.area_logger:
            self.area_logger.log_event(
                area_id,
                "mode",
                "Manual override mode active - user control",
                {"mode": "manual_override"},
            )

        # Still control switches/pumps based on actual heating state
        is_heating = device_control_handler.is_any_thermostat_actively_heating(area)
        await device_control_handler.async_control_switches(area, is_heating)

    async def async_handle_disabled_area(
        self, area_id: str, area: Area, device_handler, history_tracker, should_record_history: bool
    ) -> None:
        """Handle a disabled area - turn off devices and record history."""
        # Record history for disabled areas too
        if should_record_history and history_tracker and area.current_temperature is not None:
            await history_tracker.async_record_temperature(
                area_id, area.current_temperature, area.target_temperature, area.state
            )

        # Turn off all heating/cooling devices
        if device_handler:
            # Turn off thermostats/AC units
            await device_handler.async_control_thermostats(area, False, None)
            # Turn off switches
            await device_handler.async_control_switches(area, False)
            # Turn off valves
            await device_handler.async_control_valves(area, False, None)

        area.state = "off"

        if self.area_logger:
            self.area_logger.log_event(
                area_id,
                "mode",
                "Area disabled - all devices turned off, temperature tracking continues",
                {"mode": "disabled", "current_temperature": area.current_temperature},
            )
