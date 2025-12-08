"""Sensor monitoring for climate control."""

import logging

from homeassistant.core import HomeAssistant

from ..area_manager import AreaManager
from ..models import Area

_LOGGER = logging.getLogger(__name__)


class SensorMonitoringHandler:
    """Handle window and presence sensor monitoring."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager, area_logger=None):
        """Initialize sensor monitoring handler.

        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            area_logger: Optional area logger for events
        """
        self.hass = hass
        self.area_manager = area_manager
        self.area_logger = area_logger

    def check_window_sensors(self, area_id: str, area: Area) -> bool:
        """Check window sensor states for an area.

        Returns:
            True if any window is open
        """
        if not area.window_sensors:
            return False

        any_window_open = False
        for sensor in area.window_sensors:
            sensor_id = sensor.get("entity_id") if isinstance(sensor, dict) else sensor
            state = self.hass.states.get(sensor_id)
            if state:
                is_open = state.state in ("on", "open", "true", "True")
                if is_open:
                    any_window_open = True
                    _LOGGER.debug("Window sensor %s is open in area %s", sensor_id, area_id)

        return any_window_open

    def log_window_state_change(self, area_id: str, area: Area, any_window_open: bool) -> None:
        """Log window state changes."""
        if area.window_is_open != any_window_open:
            area.window_is_open = any_window_open
            if any_window_open:
                _LOGGER.info("Window(s) opened in area %s - temperature adjustment active", area_id)
                if self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "sensor",
                        "Window opened - temperature adjustment active",
                        {"sensor_type": "window", "state": "open"},
                    )
            else:
                _LOGGER.info("All windows closed in area %s - normal heating resumed", area_id)
                if self.area_logger:
                    self.area_logger.log_event(
                        area_id,
                        "sensor",
                        "All windows closed - normal heating resumed",
                        {"sensor_type": "window", "state": "closed"},
                    )

    def get_presence_sensors_for_area(self, area: Area) -> list:
        """Get presence sensors for an area (global or area-specific)."""
        if area.use_global_presence:
            return self.area_manager.global_presence_sensors
        return area.presence_sensors

    def check_presence_sensors(self, area_id: str, sensors: list) -> bool:
        """Check presence sensor states.

        Returns:
            True if presence is detected
        """
        if not sensors:
            return False

        any_presence_detected = False
        for sensor in sensors:
            sensor_id = sensor.get("entity_id") if isinstance(sensor, dict) else sensor
            state = self.hass.states.get(sensor_id)
            if state:
                is_present = state.state in ("on", "home", "detected", "true", "True")
                if is_present:
                    any_presence_detected = True
                    _LOGGER.debug("Presence detected by %s in area %s", sensor_id, area_id)

        return any_presence_detected

    def log_presence_state_change(self, area_id: str, any_presence_detected: bool) -> None:
        """Log presence state changes."""
        if any_presence_detected:
            _LOGGER.info("Presence detected in area %s - temperature boost active", area_id)
            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "sensor",
                    "Presence detected - temperature boost active",
                    {"sensor_type": "presence", "state": "detected"},
                )
        else:
            _LOGGER.info("No presence in area %s - boost removed", area_id)
            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "sensor",
                    "No presence detected - boost removed",
                    {"sensor_type": "presence", "state": "not_detected"},
                )

    async def handle_auto_preset_change(
        self, area_id: str, area: Area, any_presence_detected: bool
    ) -> None:
        """Handle automatic preset mode switching based on presence."""
        if not area.auto_preset_enabled:
            return

        new_preset = area.auto_preset_home if any_presence_detected else area.auto_preset_away
        if area.preset_mode != new_preset:
            old_preset = area.preset_mode
            area.preset_mode = new_preset
            await self.area_manager.async_save()
            _LOGGER.info(
                "Auto preset: %s → %s (presence %s in area %s)",
                old_preset,
                new_preset,
                "detected" if any_presence_detected else "not detected",
                area_id,
            )
            if self.area_logger:
                self.area_logger.log_event(
                    area_id,
                    "preset",
                    f"Auto preset changed: {old_preset} → {new_preset}",
                    {
                        "old_preset": old_preset,
                        "new_preset": new_preset,
                        "presence_detected": any_presence_detected,
                        "trigger": "auto_presence",
                    },
                )

    async def async_update_sensor_states(self) -> None:
        """Update window and presence sensor states for all areas."""
        for area_id, area in self.area_manager.get_all_areas().items():
            # Update window sensor states
            any_window_open = self.check_window_sensors(area_id, area)
            self.log_window_state_change(area_id, area, any_window_open)

            # Update presence sensor states
            presence_sensors = self.get_presence_sensors_for_area(area)
            any_presence_detected = self.check_presence_sensors(area_id, presence_sensors)

            # Update cached state and log if changed
            if area.presence_detected != any_presence_detected:
                area.presence_detected = any_presence_detected
                self.log_presence_state_change(area_id, any_presence_detected)

                # Auto preset mode switching
                await self.handle_auto_preset_change(area_id, area, any_presence_detected)
