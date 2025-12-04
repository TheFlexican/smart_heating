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
            
            # Add area information
            for area_id, area in areas.items():
                data["areas"][area_id] = {
                    "name": area.name,
                    "enabled": area.enabled,
                    "state": area.state,
                    "target_temperature": area.target_temperature,
                    "current_temperature": area.current_temperature,
                    "device_count": len(area.devices),
                }
            
            _LOGGER.debug("Smart Heating data updated successfully: %d areas", len(areas))
            return data
            
        except Exception as err:
            _LOGGER.error("Error updating Smart Heating data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
