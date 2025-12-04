"""DataUpdateCoordinator for the Zone Heater Manager integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, STATE_INITIALIZED, UPDATE_INTERVAL
from .zone_manager import ZoneManager

_LOGGER = logging.getLogger(__name__)


class ZoneHeaterManagerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Zone Heater Manager data."""

    def __init__(self, hass: HomeAssistant, zone_manager: ZoneManager) -> None:
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            zone_manager: Zone manager instance
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.zone_manager = zone_manager
        _LOGGER.debug("ZoneHeaterManagerCoordinator initialized")

    async def _async_update_data(self) -> dict:
        """Fetch data from the integration.
        
        This is the place to fetch and process the data from your source.
        Updates zone temperatures from MQTT devices.
        
        Returns:
            dict: Dictionary containing the current state
            
        Raises:
            UpdateFailed: If update fails
        """
        try:
            _LOGGER.debug("Updating Zone Heater Manager data")
            
            # Get all zones
            zones = self.zone_manager.get_all_zones()
            
            # Build data structure
            data = {
                "status": STATE_INITIALIZED,
                "zone_count": len(zones),
                "zones": {},
            }
            
            # Add zone information
            for zone_id, zone in zones.items():
                data["zones"][zone_id] = {
                    "name": zone.name,
                    "enabled": zone.enabled,
                    "state": zone.state,
                    "target_temperature": zone.target_temperature,
                    "current_temperature": zone.current_temperature,
                    "device_count": len(zone.devices),
                }
            
            _LOGGER.debug("Zone Heater Manager data updated successfully: %d zones", len(zones))
            return data
            
        except Exception as err:
            _LOGGER.error("Error updating Zone Heater Manager data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
