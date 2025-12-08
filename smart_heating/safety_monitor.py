"""Safety monitoring for Smart Heating integration.

Monitors smoke and carbon monoxide sensors to trigger emergency heating shutdown.
"""
import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.event import async_track_state_change_event

if TYPE_CHECKING:
    from .area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class SafetyMonitor:
    """Monitor safety sensors and trigger emergency shutdown when needed."""

    def __init__(self, hass: HomeAssistant, area_manager: "AreaManager") -> None:
        """Initialize the safety monitor.
        
        Args:
            hass: Home Assistant instance
            area_manager: Area manager instance
        """
        self.hass = hass
        self.area_manager = area_manager
        self._state_unsub = None
        self._emergency_shutdown_active = False
        _LOGGER.debug("SafetyMonitor initialized")

    async def async_setup(self) -> None:
        """Set up the safety monitor with state change listeners."""
        _LOGGER.warning("SafetyMonitor async_setup called")
        await self._setup_state_listener()

    async def _setup_state_listener(self) -> None:
        """Set up state change listeners for all safety sensors."""
        # Remove existing listener if any
        if self._state_unsub:
            self._state_unsub()
            self._state_unsub = None
        
        # Get all configured safety sensors
        safety_sensors = self.area_manager.get_safety_sensors()
        
        # Filter for enabled sensors
        enabled_sensors = [s for s in safety_sensors if s.get("enabled", True)]
        
        _LOGGER.warning("Setting up listeners for %d enabled safety sensors", len(enabled_sensors))
        
        if enabled_sensors:
            # Collect all sensor IDs
            sensor_ids = [s["sensor_id"] for s in enabled_sensors]
            
            _LOGGER.warning("Monitoring safety sensors: %s", sensor_ids)
            
            # Check if sensors exist
            for sensor_id in sensor_ids:
                sensor_state = self.hass.states.get(sensor_id)
                if sensor_state:
                    _LOGGER.warning("Sensor %s exists! Current state: %s", sensor_id, sensor_state.state)
                else:
                    _LOGGER.warning("WARNING: Sensor %s does not exist yet!", sensor_id)
            
            # Set up listener for all sensors
            self._state_unsub = async_track_state_change_event(
                self.hass,
                sensor_ids,
                self._handle_safety_sensor_state_change
            )
            _LOGGER.warning("Safety sensor listeners registered successfully for %d sensors", len(sensor_ids))
            
            # Check initial state
            await self._check_safety_status()
        else:
            _LOGGER.warning("No enabled safety sensors configured, skipping listener setup")

    @callback
    def _handle_safety_sensor_state_change(self, event: Event) -> None:
        """Handle state changes of safety sensor.
        
        Args:
            event: State change event
        """
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        _LOGGER.warning("🔥 SAFETY SENSOR STATE CHANGE DETECTED!")
        _LOGGER.warning("Entity: %s", entity_id)
        _LOGGER.warning("Old state: %s", old_state.state if old_state else "None")
        _LOGGER.warning("New state: %s", new_state.state if new_state else "None")
        
        if not new_state:
            return
        
        # Check for alert condition
        self.hass.async_create_task(self._check_safety_status())

    async def _check_safety_status(self) -> None:
        """Check safety sensor status and trigger shutdown if needed."""
        is_alert, alerting_sensor_id = self.area_manager.check_safety_sensor_status()
        
        if is_alert and not self._emergency_shutdown_active:
            # Safety alert detected - trigger emergency shutdown
            _LOGGER.error(
                "\ud83d\udea8 SAFETY ALERT DETECTED on %s! Triggering emergency heating shutdown!",
                alerting_sensor_id
            )
            await self._trigger_emergency_shutdown(alerting_sensor_id)
            
        elif not is_alert and self._emergency_shutdown_active:
            # Alert cleared - log but keep shutdown active (manual intervention required)
            _LOGGER.warning(
                "All safety alerts cleared. Emergency shutdown remains active - manual intervention required."
            )

    async def _trigger_emergency_shutdown(self, alerting_sensor_id: str) -> None:
        """Trigger emergency shutdown of all heating.
        
        Args:
            alerting_sensor_id: The sensor ID that triggered the alert
        """
        self._emergency_shutdown_active = True
        self.area_manager.set_safety_alert_active(True)
        
        _LOGGER.error("=" * 80)
        _LOGGER.error("EMERGENCY HEATING SHUTDOWN INITIATED")
        _LOGGER.error("Reason: Safety sensor alert detected")
        _LOGGER.error("Sensor: %s", alerting_sensor_id)
        _LOGGER.error("=" * 80)
        
        # Disable all areas
        disabled_count = 0
        for area in self.area_manager.get_all_areas().values():
            if area.enabled:
                area.enabled = False
                disabled_count += 1
                _LOGGER.error("Area '%s' disabled due to safety alert", area.name)
        
        # Save configuration to persist disabled state
        await self.area_manager.async_save()
        
        _LOGGER.error(
            "Emergency shutdown complete: %d areas disabled. "
            "All areas must be manually re-enabled after safety issue is resolved.",
            disabled_count
        )
        
        # Fire event for WebSocket notification
        self.hass.bus.async_fire(
            "smart_heating_safety_alert",
            {
                "sensor_id": alerting_sensor_id,
                "areas_disabled": disabled_count,
                "message": "Emergency heating shutdown due to safety sensor alert"
            }
        )
        
        # Request coordinator refresh to update frontend immediately
        from .const import DOMAIN
        entry_ids = [
            key for key in self.hass.data[DOMAIN].keys()
            if key not in ["history", "climate_controller", "schedule_executor", 
                          "learning_engine", "area_logger", "vacation_manager", "safety_monitor"]
        ]
        if entry_ids:
            coordinator = self.hass.data[DOMAIN][entry_ids[0]]
            await coordinator.async_request_refresh()
            _LOGGER.info("Coordinator refresh requested after emergency shutdown")

    async def async_reconfigure(self) -> None:
        """Reconfigure safety monitor when sensor settings change."""
        _LOGGER.info("Reconfiguring safety monitor")
        await self._setup_state_listener()
        
        # Check current status
        await self._check_safety_status()

    def async_shutdown(self) -> None:
        """Shutdown safety monitor and clean up listeners."""
        if self._state_unsub:
            self._state_unsub()
            self._state_unsub = None
        _LOGGER.debug("SafetyMonitor shutdown")

    def reset_emergency_shutdown(self) -> None:
        """Reset emergency shutdown state (for manual recovery).
        
        Note: Areas remain disabled and must be manually re-enabled.
        """
        _LOGGER.warning("Emergency shutdown state reset - areas remain disabled")
        self._emergency_shutdown_active = False
        self.area_manager.set_safety_alert_active(False)
