"""DataUpdateCoordinator for the Smart Heating integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, STATE_INITIALIZED, UPDATE_INTERVAL
from .area_manager import AreaManager

_LOGGER = logging.getLogger(__name__)


class SmartHeatingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Smart Heating data."""

    def __init__(self, hass: HomeAssistant, area_manager: AreaManager) -> None:
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            area_manager: Zone manager instance
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.area_manager = area_manager
        _LOGGER.debug("Smart Heating coordinator initialized")

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
            _LOGGER.debug("Updating Smart Heating data")
            
            # Get all areas
            areas = self.area_manager.get_all_areas()
            
            # Build data structure
            data = {
                "status": STATE_INITIALIZED,
                "area_count": len(areas),
                "areas": {},
            }
            
            # Add area information with device states
            for area_id, area in areas.items():
                # Get device states
                devices_data = []
                for device_id, device_info in area.devices.items():
                    state = self.hass.states.get(device_id)
                    device_data = {
                        "id": device_id,
                        "type": device_info["type"],
                        "state": state.state if state else "unavailable",
                    }
                    
                    # Add device-specific attributes
                    if state:
                        if device_info["type"] == "thermostat":
                            device_data["current_temperature"] = state.attributes.get("current_temperature")
                            device_data["target_temperature"] = state.attributes.get("temperature")
                            device_data["hvac_action"] = state.attributes.get("hvac_action")
                        elif device_info["type"] == "temperature_sensor":
                            # For temperature sensors, the state IS the temperature
                            try:
                                temp_value = float(state.state) if state.state not in ("unknown", "unavailable") else None
                                if temp_value is not None:
                                    # Check if temperature is in Fahrenheit and convert to Celsius
                                    unit = state.attributes.get("unit_of_measurement", "°C")
                                    if unit in ("°F", "F"):
                                        temp_value = (temp_value - 32) * 5/9
                                        _LOGGER.debug(
                                            "Converted temperature sensor %s: %s°F -> %.1f°C",
                                            device_id, state.state, temp_value
                                        )
                                    device_data["temperature"] = temp_value
                                else:
                                    device_data["temperature"] = None
                            except (ValueError, TypeError):
                                device_data["temperature"] = None
                        elif device_info["type"] == "valve":
                            # For valves (number entities), the position is in the state
                            try:
                                device_data["position"] = float(state.state) if state.state not in ("unknown", "unavailable") else None
                            except (ValueError, TypeError):
                                device_data["position"] = None
                    
                    devices_data.append(device_data)
                
                data["areas"][area_id] = {
                    "name": area.name,
                    "enabled": area.enabled,
                    "state": area.state,
                    "target_temperature": area.target_temperature,
                    "current_temperature": area.current_temperature,
                    "device_count": len(area.devices),
                    "devices": devices_data,
                }
            
            _LOGGER.debug("Smart Heating data updated successfully: %d areas", len(areas))
            return data
            
        except Exception as err:
            _LOGGER.error("Error updating Smart Heating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
