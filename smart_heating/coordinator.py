"""DataUpdateCoordinator for the Smart Heating integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import ATTR_ENTITY_ID

from .const import DOMAIN, STATE_INITIALIZED, UPDATE_INTERVAL
from .area_manager import AreaManager
from .models import Area

_LOGGER = logging.getLogger(__name__)

# Debounce delay for manual temperature changes (in seconds)
MANUAL_TEMP_CHANGE_DEBOUNCE = 2.0


class SmartHeatingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Smart Heating data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, area_manager: AreaManager) -> None:
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            entry: Config entry
            area_manager: Zone manager instance
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.area_manager = area_manager
        self._unsub_state_listener = None
        self._debounce_tasks = {}  # Track debounce tasks per entity
        _LOGGER.debug("Smart Heating coordinator initialized")

    async def async_setup(self) -> None:
        """Set up the coordinator with state change listeners."""
        _LOGGER.debug("Coordinator async_setup called")
        # Get all device entity IDs that we need to track
        tracked_entities = []
        areas = self.area_manager.get_all_areas()
        _LOGGER.warning("Found %d areas to process", len(areas))
        for area in areas.values():
            for device_id in area.devices.keys():
                tracked_entities.append(device_id)
        
        if tracked_entities:
            _LOGGER.warning("Setting up state change listeners for %d devices: %s", len(tracked_entities), tracked_entities[:5])
            self._unsub_state_listener = async_track_state_change_event(
                self.hass,
                tracked_entities,
                self._handle_state_change
            )
            _LOGGER.warning("State change listeners successfully registered")
        else:
            _LOGGER.warning("No devices found to track for state changes")
        
        # Do initial update
        await self.async_refresh()
        _LOGGER.debug("Coordinator async_setup completed")

    @callback
    def _should_update_for_state_change(
        self, entity_id: str, old_state, new_state
    ) -> bool:
        """Determine if a state change should trigger coordinator update.
        
        Args:
            entity_id: Entity ID that changed
            old_state: Previous state
            new_state: New state
            
        Returns:
            True if update should be triggered
        """
        if old_state is None:
            # Initial state, trigger update
            return True
        
        if old_state.state != new_state.state:
            # State changed
            _LOGGER.debug("State changed for %s: %s -> %s", entity_id, old_state.state, new_state.state)
            return True
        
        if old_state.attributes.get('current_temperature') != new_state.attributes.get('current_temperature'):
            # Current temperature changed
            _LOGGER.debug(
                "Current temperature changed for %s: %s -> %s",
                entity_id,
                old_state.attributes.get('current_temperature'),
                new_state.attributes.get('current_temperature')
            )
            return True
        
        if old_state.attributes.get('hvac_action') != new_state.attributes.get('hvac_action'):
            # HVAC action changed (heating/idle/off)
            _LOGGER.info(
                "HVAC action changed for %s: %s -> %s",
                entity_id,
                old_state.attributes.get('hvac_action'),
                new_state.attributes.get('hvac_action')
            )
            return True
        
        return False

    def _handle_temperature_change(
        self, entity_id: str, old_state, new_state
    ) -> None:
        """Handle debounced temperature changes from thermostats.
        
        Args:
            entity_id: Entity ID
            old_state: Previous state
            new_state: New state
        """
        new_temp = new_state.attributes.get('temperature')
        old_temp = old_state.attributes.get('temperature')
        
        _LOGGER.warning(
            "Thermostat temperature change detected for %s: %s -> %s (debouncing)",
            entity_id,
            old_temp,
            new_temp
        )
        
        # Cancel any existing debounce task for this entity
        if entity_id in self._debounce_tasks:
            self._debounce_tasks[entity_id].cancel()
        
        # Create new debounced task
        async def debounced_temp_update():
            """Update area after debounce delay."""
            try:
                await asyncio.sleep(MANUAL_TEMP_CHANGE_DEBOUNCE)
                
                _LOGGER.warning(
                    "Applying debounced temperature change for %s: %s",
                    entity_id,
                    new_temp
                )
                
                await self._apply_manual_temperature_change(entity_id, new_temp)
                
                # Force immediate coordinator refresh after debounce (not rate-limited)
                _LOGGER.debug("Forcing coordinator refresh after debounce")
                await self.async_refresh()
                _LOGGER.debug("Coordinator refresh completed")
                
            except asyncio.CancelledError:
                _LOGGER.warning("Debounce task cancelled for %s", entity_id)
                raise
            except Exception as err:
                _LOGGER.error("Error in debounced temperature update: %s", err, exc_info=True)
            finally:
                # Clean up task reference
                if entity_id in self._debounce_tasks:
                    del self._debounce_tasks[entity_id]
        
        # Store and start the debounce task
        import asyncio
        self._debounce_tasks[entity_id] = asyncio.create_task(debounced_temp_update())

    async def _apply_manual_temperature_change(
        self, entity_id: str, new_temp: float
    ) -> None:
        """Apply manual temperature change to area.
        
        Args:
            entity_id: Thermostat entity ID
            new_temp: New temperature set by user
        """
        # Update area target temperature AND set manual override flag
        # BUT only if this is truly a manual change (not from a schedule/preset)
        for area in self.area_manager.get_all_areas().values():
            if entity_id in area.devices:
                # Check if the temperature change matches the area's current target
                # If it does, this is likely from a schedule or preset, not manual
                expected_temp = area.get_effective_target_temperature()
                
                # Allow 0.1°C tolerance for floating point comparison
                if abs(new_temp - expected_temp) < 0.1:
                    _LOGGER.info(
                        "Temperature change for %s matches expected %.1f°C - ignoring (not manual)",
                        area.name,
                        expected_temp
                    )
                    break
                
                # IMPORTANT: Ignore temperature changes that are LOWER than current target
                # These are typically stale state changes from old preset values that arrive
                # AFTER a schedule has already updated the area target to a higher value.
                # This prevents false manual override triggers during schedule transitions.
                if new_temp < expected_temp - 0.1:
                    _LOGGER.info(
                        "Temperature change for %s is %.1f°C < expected %.1f°C - likely stale state from old preset, ignoring",
                        area.name,
                        new_temp,
                        expected_temp
                    )
                    break
                
                # This is a true manual change - enter manual override mode
                _LOGGER.warning(
                    "Area %s entering MANUAL OVERRIDE mode - thermostat changed to %.1f°C (expected %.1f°C)",
                    area.name,
                    new_temp,
                    expected_temp
                )
                area.target_temperature = new_temp
                area.manual_override = True  # Enter manual override mode
                # Save to storage so it persists across restarts
                await self.area_manager.async_save()
                break

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state changes of tracked entities.
        
        Args:
            event: State change event
        """
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        if not new_state:
            return
        
        # Check for target temperature changes (for thermostats) - handle with debouncing
        if (old_state and 
            old_state.attributes.get('temperature') != new_state.attributes.get('temperature')):
            self._handle_temperature_change(entity_id, old_state, new_state)
            return  # Don't trigger immediate update - wait for debounce
        
        # Check if other state changes should trigger update
        if self._should_update_for_state_change(entity_id, old_state, new_state):
            # Trigger immediate coordinator update
            _LOGGER.debug("Triggering coordinator refresh for %s", entity_id)
            import asyncio
            asyncio.create_task(self.async_request_refresh())

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and clean up listeners."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None
        _LOGGER.debug("Smart Heating coordinator shutdown")

    def _get_device_state_data(self, device_id: str, device_info: dict) -> dict:
        """Get state data for a single device.
        
        Args:
            device_id: Device entity ID
            device_info: Device information from area
            
        Returns:
            Device state data dictionary
        """
        state = self.hass.states.get(device_id)
        device_data = {
            "id": device_id,
            "type": device_info["type"],
            "state": state.state if state else "unavailable",
            "name": state.attributes.get("friendly_name", device_id) if state else device_id,
        }
        
        if not state:
            return device_data
        
        # Add device-specific attributes based on type
        if device_info["type"] == "thermostat":
            device_data.update({
                "current_temperature": state.attributes.get("current_temperature"),
                "target_temperature": state.attributes.get("temperature"),
                "hvac_action": state.attributes.get("hvac_action")
            })
        elif device_info["type"] == "temperature_sensor":
            device_data["temperature"] = self._get_temperature_from_sensor(device_id, state)
        elif device_info["type"] == "valve":
            device_data["position"] = self._get_valve_position(state)
        
        return device_data

    def _get_temperature_from_sensor(self, device_id: str, state) -> Optional[float]:
        """Extract and convert temperature from sensor state.
        
        Args:
            device_id: Sensor entity ID
            state: Home Assistant state object
            
        Returns:
            Temperature in Celsius or None
        """
        try:
            temp_value = float(state.state) if state.state not in ("unknown", "unavailable") else None
            if temp_value is None:
                return None
            
            # Check if temperature is in Fahrenheit and convert to Celsius
            unit = state.attributes.get("unit_of_measurement", "°C")
            if unit in ("°F", "F"):
                temp_value = (temp_value - 32) * 5/9
                _LOGGER.debug(
                    "Converted temperature sensor %s: %s°F -> %.1f°C",
                    device_id, state.state, temp_value
                )
            return temp_value
        except (ValueError, TypeError):
            return None

    def _get_valve_position(self, state) -> Optional[float]:
        """Extract valve position from state.
        
        Args:
            state: Home Assistant state object
            
        Returns:
            Valve position or None
        """
        try:
            return float(state.state) if state.state not in ("unknown", "unavailable") else None
        except (ValueError, TypeError):
            return None

    def _build_area_data(self, area_id: str, area: Area) -> dict:
        """Build data dictionary for a single area.
        
        Args:
            area_id: Area identifier
            area: Area instance
            
        Returns:
            Area data dictionary
        """
        # Get device states
        devices_data = []
        for device_id, device_info in area.devices.items():
            device_data = self._get_device_state_data(device_id, device_info)
            devices_data.append(device_data)
        
        _LOGGER.debug(
            "Building data for area %s: manual_override=%s, target_temp=%s",
            area_id, getattr(area, 'manual_override', False), area.target_temperature
        )
        
        return {
            "id": area_id,  # Include area ID so frontend can identify and navigate
            "name": area.name,
            "enabled": area.enabled,
            "state": area.state,
            "target_temperature": area.target_temperature,
            "effective_target_temperature": area.get_effective_target_temperature(),
            "current_temperature": area.current_temperature,
            "device_count": len(area.devices),
            "devices": devices_data,
            # Schedules
            "schedules": [s.to_dict() for s in area.schedules.values()],
            # Preset mode settings
            "preset_mode": area.preset_mode,
            "away_temp": area.away_temp,
            "eco_temp": area.eco_temp,
            "comfort_temp": area.comfort_temp,
            "home_temp": area.home_temp,
            "sleep_temp": area.sleep_temp,
            "activity_temp": area.activity_temp,
            # Global preset flags
            "use_global_away": area.use_global_away,
            "use_global_eco": area.use_global_eco,
            "use_global_comfort": area.use_global_comfort,
            "use_global_home": area.use_global_home,
            "use_global_sleep": area.use_global_sleep,
            "use_global_activity": area.use_global_activity,
            # Global presence flag
            "use_global_presence": area.use_global_presence,
            # Boost mode
            "boost_mode_active": area.boost_mode_active,
            "boost_temp": area.boost_temp,
            "boost_duration": area.boost_duration,
            # HVAC mode
            "hvac_mode": area.hvac_mode,
            # Hysteresis override
            "hysteresis_override": area.hysteresis_override,
            # Manual override
            "manual_override": getattr(area, 'manual_override', False),
            # Hidden state (frontend-only, but persisted in backend)
            "hidden": getattr(area, 'hidden', False),
            # Switch/pump control
            "shutdown_switches_when_idle": getattr(area, 'shutdown_switches_when_idle', True),
            # Sensors
            "window_sensors": area.window_sensors,
            "presence_sensors": area.presence_sensors,
            # Night boost
            "night_boost_enabled": area.night_boost_enabled,
            "night_boost_offset": area.night_boost_offset,
            "night_boost_start_time": area.night_boost_start_time,
            "night_boost_end_time": area.night_boost_end_time,
            # Smart night boost
            "smart_night_boost_enabled": area.smart_night_boost_enabled,
            "smart_night_boost_target_time": area.smart_night_boost_target_time,
            "weather_entity_id": area.weather_entity_id,
            # Primary temperature sensor
            "primary_temperature_sensor": area.primary_temperature_sensor,
        }

    async def _async_update_data(self) -> dict:
        """Fetch data from the integration.
        
        This is the place to fetch and process the data from your source.
        Updates area temperatures from MQTT devices.
        
        Returns:
            dict: Dictionary containing the current state
            
        Raises:
            UpdateFailed: If update fails
        """
        try:
            _LOGGER.debug("Coordinator update data called")
            
            # Get all areas
            areas = self.area_manager.get_all_areas()
            _LOGGER.debug("Processing %d areas for coordinator update", len(areas))
            
            # Build data structure
            data = {
                "status": STATE_INITIALIZED,
                "area_count": len(areas),
                "areas": {},
            }
            
            # Add area information with device states
            for area_id, area in areas.items():
                data["areas"][area_id] = self._build_area_data(area_id, area)
            
            _LOGGER.debug("Smart Heating data updated successfully: %d areas", len(areas))
            return data
            
        except Exception as err:
            _LOGGER.error("Error updating Smart Heating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
