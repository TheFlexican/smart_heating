"""Climate controller for Smart Heating - Refactored."""
import logging
from datetime import datetime
from typing import Optional

from homeassistant.core import HomeAssistant

from .area_manager import AreaManager
from .climate_handlers import (
    TemperatureSensorHandler,
    DeviceControlHandler,
    SensorMonitoringHandler,
    ProtectionHandler,
    HeatingCycleHandler,
)

_LOGGER = logging.getLogger(__name__)


class ClimateController:
    """Control heating based on area settings and schedules."""

    def __init__(
        self, hass: HomeAssistant, area_manager: AreaManager, learning_engine=None
    ) -> None:
        """Initialize the climate controller.
        
        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
            learning_engine: Optional learning engine for adaptive features
        """
        self.hass = hass
        self.area_manager = area_manager
        self.learning_engine = learning_engine
        self._hysteresis = 0.5  # Temperature hysteresis in °C
        
        # Initialize handlers
        self.temp_handler = TemperatureSensorHandler(hass)
        self.device_handler = DeviceControlHandler(hass, area_manager)
        self.sensor_handler = None  # Set by set_area_logger
        self.protection_handler = None  # Set by set_area_logger
        self.cycle_handler = None  # Set by set_area_logger

    def set_area_logger(self, area_logger) -> None:
        """Set area logger and reinitialize handlers that need it.
        
        Args:
            area_logger: Area logger instance
        """
        self.area_logger = area_logger
        self.sensor_handler = SensorMonitoringHandler(
            self.hass, self.area_manager, area_logger
        )
        self.protection_handler = ProtectionHandler(
            self.hass, self.area_manager, area_logger
        )
        self.cycle_handler = HeatingCycleHandler(
            self.hass, self.area_manager, self.learning_engine, area_logger
        )

    # Delegate methods to handlers for backward compatibility with tests
    def _get_temperature_from_sensor(self, sensor_id: str) -> Optional[float]:
        """Get temperature from sensor (delegates to handler)."""
        return self.temp_handler.get_temperature_from_sensor(sensor_id)

    def _get_temperature_from_thermostat(self, thermostat_id: str) -> Optional[float]:
        """Get temperature from thermostat (delegates to handler)."""
        return self.temp_handler.get_temperature_from_thermostat(thermostat_id)

    def _collect_area_temperatures(self, area):
        """Collect area temperatures (delegates to handler)."""
        return self.temp_handler.collect_area_temperatures(area)

    def _convert_fahrenheit_to_celsius(self, temp: float) -> float:
        """Convert Fahrenheit to Celsius (delegates to handler)."""
        return self.temp_handler.convert_fahrenheit_to_celsius(temp)

    def _get_temperature_from_sensor(self, sensor_id: str) -> Optional[float]:
        """Get temperature from sensor (delegates to handler)."""
        return self.temp_handler.get_temperature_from_sensor(sensor_id)

    def _check_window_sensors(self, area_id: str, area) -> bool:
        """Check window sensors (delegates to handler)."""
        if not self.sensor_handler:
            return False
        return self.sensor_handler.check_window_sensors(area_id, area)

    def _log_window_state_change(self, area_id: str, area, any_window_open: bool) -> None:
        """Log window state change (delegates to handler)."""
        if self.sensor_handler:
            self.sensor_handler.log_window_state_change(area_id, area, any_window_open)

    def _get_presence_sensors_for_area(self, area):
        """Get presence sensors for area (delegates to handler)."""
        if not self.sensor_handler:
            return []
        return self.sensor_handler.get_presence_sensors_for_area(area)

    def _check_presence_sensors(self, area_id: str, sensors: list) -> bool:
        """Check presence sensors (delegates to handler)."""
        if not self.sensor_handler:
            return False
        return self.sensor_handler.check_presence_sensors(area_id, sensors)

    async def _handle_auto_preset_change(self, area_id: str, area, presence: bool) -> None:
        """Handle auto preset change (delegates to handler)."""
        if self.sensor_handler:
            await self.sensor_handler.handle_auto_preset_change(area_id, area, presence)

    async def _async_prepare_heating_cycle(self):
        """Prepare heating cycle (delegates to handler)."""
        if not self.cycle_handler:
            return False, None
        return await self.cycle_handler.async_prepare_heating_cycle(
            self.temp_handler, self.sensor_handler
        )

    def _is_any_thermostat_actively_heating(self, area) -> bool:
        """Check if thermostats are heating (delegates to handler)."""
        return self.device_handler.is_any_thermostat_actively_heating(area)

    def _get_valve_capability(self, entity_id: str):
        """Get valve capability (delegates to handler)."""
        return self.device_handler.get_valve_capability(entity_id)

    def _apply_frost_protection(self, area_id: str, target_temp: float) -> float:
        """Apply frost protection (delegates to handler)."""
        if not self.protection_handler:
            return target_temp
        return self.protection_handler.apply_frost_protection(area_id, target_temp)

    def _apply_vacation_mode(self, area_id: str, area) -> None:
        """Apply vacation mode (delegates to handler)."""
        if self.protection_handler:
            self.protection_handler.apply_vacation_mode(area_id, area)

    async def _async_control_thermostats(self, area, heating: bool, target_temp: Optional[float]) -> None:
        """Control thermostats (delegates to handler)."""
        await self.device_handler.async_control_thermostats(area, heating, target_temp)

    async def _async_control_switches(self, area, heating: bool) -> None:
        """Control switches (delegates to handler)."""
        await self.device_handler.async_control_switches(area, heating)

    async def _async_control_valves(self, area, heating: bool, target_temp: Optional[float]) -> None:
        """Control valves (delegates to handler)."""
        await self.device_handler.async_control_valves(area, heating, target_temp)

    async def _async_control_opentherm_gateway(self, any_heating: bool, max_target_temp: float) -> None:
        """Control OpenTherm gateway (delegates to handler)."""
        await self.device_handler.async_control_opentherm_gateway(any_heating, max_target_temp)

    async def _async_get_outdoor_temperature(self, area):
        """Get outdoor temperature (delegates to handler)."""
        return await self.temp_handler.async_get_outdoor_temperature(area)

    async def _async_handle_manual_override(self, area_id: str, area) -> None:
        """Handle manual override (delegates to handler)."""
        if self.protection_handler:
            await self.protection_handler.async_handle_manual_override(
                area_id, area, self.device_handler
            )

    async def _async_handle_disabled_area(
        self, area_id: str, area, history_tracker, should_record_history: bool
    ) -> None:
        """Handle disabled area (delegates to handler)."""
        if self.protection_handler:
            await self.protection_handler.async_handle_disabled_area(
                area_id, area, history_tracker, should_record_history
            )

    async def async_update_area_temperatures(self) -> None:
        """Update current temperatures for all areas from sensors."""
        for area_id, area in self.area_manager.get_all_areas().items():
            temp_sensors = area.get_temperature_sensors()
            thermostats = area.get_thermostats()
            
            if not temp_sensors and not thermostats:
                continue
            
            temps = self.temp_handler.collect_area_temperatures(area)
            
            if temps:
                avg_temp = sum(temps) / len(temps)
                area.current_temperature = avg_temp
                _LOGGER.debug(
                    "Area %s temperature: %.1f°C (from %d sensors)",
                    area_id, avg_temp, len(temps)
                )

    async def _async_set_area_heating(self, area, heating: bool, target_temp: Optional[float] = None) -> None:
        """Set heating state for an area."""
        await self.device_handler.async_control_thermostats(area, heating, target_temp)
        await self.device_handler.async_control_switches(area, heating)
        await self.device_handler.async_control_valves(area, heating, target_temp)

    async def async_control_heating(self) -> None:
        """Control heating for all areas based on temperature and schedules."""
        if not self.cycle_handler or not self.protection_handler:
            _LOGGER.error("Handlers not initialized - call set_area_logger first")
            return

        current_time = datetime.now()
        
        # Prepare for heating cycle
        should_record_history, history_tracker = await self.cycle_handler.async_prepare_heating_cycle(
            self.temp_handler, self.sensor_handler
        )
        
        # Track heating demands across all areas
        heating_areas = []
        max_target_temp = 0.0
        
        # Control each area
        for area_id, area in self.area_manager.get_all_areas().items():
            # Record history for ALL areas
            if should_record_history and history_tracker and area.current_temperature is not None:
                await history_tracker.async_record_temperature(
                    area_id, 
                    area.current_temperature, 
                    area.target_temperature, 
                    area.state
                )
            
            if not area.enabled:
                await self.protection_handler.async_handle_disabled_area(
                    area_id, area, history_tracker, should_record_history
                )
                continue
            
            # Check for manual override mode
            if hasattr(area, 'manual_override') and area.manual_override:
                await self.protection_handler.async_handle_manual_override(
                    area_id, area, self.device_handler
                )
                continue
            
            # Check for vacation mode
            self.protection_handler.apply_vacation_mode(area_id, area)
            
            # Get effective target temperature
            target_temp = area.get_effective_target_temperature(current_time)
            _LOGGER.info(
                "Area %s: Effective target=%.1f°C (boost_active=%s, preset=%s)",
                area_id, target_temp, area.boost_mode_active, area.preset_mode
            )
            
            if hasattr(self, 'area_logger') and self.area_logger:
                details = {
                    "target_temp": target_temp,
                    "boost_active": area.boost_mode_active,
                    "preset_mode": area.preset_mode,
                    "base_target": area.target_temperature
                }
                self.area_logger.log_event(
                    area_id,
                    "temperature",
                    f"Effective target temperature: {target_temp:.1f}°C",
                    details
                )
            
            # Apply frost protection
            target_temp = self.protection_handler.apply_frost_protection(area_id, target_temp)
            
            # Apply HVAC mode
            if hasattr(area, 'hvac_mode') and area.hvac_mode == "off":
                await self._async_set_area_heating(area, False)
                area.state = "off"
                _LOGGER.debug("Area %s: HVAC mode is OFF - skipping", area_id)
                continue
            
            current_temp = area.current_temperature
            
            if current_temp is None:
                _LOGGER.warning("No temperature data for area %s", area_id)
                continue
            
            # Get hysteresis
            hysteresis = area.hysteresis_override if area.hysteresis_override is not None else self._hysteresis
            
            # Determine if heating is needed
            should_heat = current_temp < (target_temp - hysteresis)
            should_stop = current_temp >= target_temp
            
            # Log hysteresis decision
            if hasattr(self, 'area_logger') and self.area_logger:
                if not should_heat and current_temp < target_temp:
                    self.area_logger.log_event(
                        area_id,
                        "climate_control",
                        f"Waiting for hysteresis ({hysteresis:.1f}°C) - not heating yet",
                        {
                            "current_temp": current_temp,
                            "target_temp": target_temp,
                            "hysteresis": hysteresis,
                            "threshold": target_temp - hysteresis,
                            "reason": "Within hysteresis band - prevents short cycling"
                        }
                    )
            
            if should_heat:
                area_heating, area_max_temp = await self.cycle_handler.async_handle_heating_required(
                    area_id, area, current_temp, target_temp,
                    self.device_handler, self.temp_handler
                )
                heating_areas.extend(area_heating)
                max_target_temp = max(max_target_temp, area_max_temp)
            elif should_stop:
                await self.cycle_handler.async_handle_heating_stop(
                    area_id, area, current_temp, target_temp,
                    self.device_handler
                )
        
        # Control OpenTherm gateway
        await self.device_handler.async_control_opentherm_gateway(
            len(heating_areas) > 0, max_target_temp
        )
        
        # Save history periodically
        if should_record_history and history_tracker:
            await history_tracker.async_save()
