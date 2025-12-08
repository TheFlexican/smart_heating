"""Device registry utilities for Smart Heating."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
)
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)

_LOGGER = logging.getLogger(__name__)


class DeviceRegistry:
    """Helper class for device discovery and management."""

    def __init__(self, hass: HomeAssistant):
        """Initialize device registry helper.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self._entity_registry = er.async_get(hass)
        self._device_registry = dr.async_get(hass)
        self._area_registry = ar.async_get(hass)

    def get_device_type(self, entity: er.RegistryEntry, state: Any) -> Optional[Tuple[str, str]]:
        """Determine device type and subtype from entity.

        Args:
            entity: Entity registry entry
            state: Entity state object

        Returns:
            Tuple of (device_type, subtype) or None if not supported
        """
        device_class = state.attributes.get("device_class")

        if entity.domain == "climate":
            return ("thermostat", "climate")
        elif entity.domain == "switch":
            return ("switch", "switch")
        elif entity.domain == "number":
            return ("number", "number")
        elif entity.domain == "sensor":
            # Only include temperature sensors
            unit = state.attributes.get("unit_of_measurement", "")
            if device_class == "temperature" or unit in ["°C", "°F"]:
                return ("sensor", "temperature")

        return None

    def get_ha_area(self, entity: er.RegistryEntry) -> Optional[Tuple[str, str]]:
        """Get Home Assistant area for an entity.

        Args:
            entity: Entity registry entry

        Returns:
            Tuple of (area_id, area_name) or None if no area assigned
        """
        if not entity.device_id:
            return None

        device_entry = self._device_registry.async_get(entity.device_id)
        if not device_entry or not device_entry.area_id:
            return None

        area_entry = self._area_registry.async_get_area(device_entry.area_id)
        if not area_entry:
            return None

        return (area_entry.id, area_entry.name)

    def should_filter_device(
        self,
        entity_id: str,
        friendly_name: str,
        ha_area_name: Optional[str],
        hidden_areas: List[Dict[str, str]],
    ) -> bool:
        """Check if device should be filtered from discovery.

        Args:
            entity_id: Entity ID
            friendly_name: Friendly name of entity
            ha_area_name: Home Assistant area name (if any)
            hidden_areas: List of hidden area dicts with 'id' and 'name'

        Returns:
            True if device should be filtered
        """
        entity_id_lower = entity_id.lower()
        friendly_name_lower = friendly_name.lower()

        for hidden_area in hidden_areas:
            area_name_lower = hidden_area["name"].lower()

            # Check if entity name contains hidden area name
            if area_name_lower in entity_id_lower or area_name_lower in friendly_name_lower:
                _LOGGER.debug(
                    "Filtering device %s - contains hidden area name '%s'",
                    entity_id,
                    hidden_area["name"],
                )
                return True

            # Check if HA area matches hidden area
            if ha_area_name and ha_area_name.lower() == area_name_lower:
                _LOGGER.debug(
                    "Filtering device %s - HA area %s matches hidden area", entity_id, ha_area_name
                )
                return True

        return False


def build_device_dict(
    entity: er.RegistryEntry,
    state: Any,
    device_type: str,
    subtype: str,
    ha_area: Optional[Tuple[str, str]],
    assigned_areas: List[str],
) -> Dict[str, Any]:
    """Build device information dictionary.

    Args:
        entity: Entity registry entry
        state: Entity state object
        device_type: Device type
        subtype: Device subtype
        ha_area: Tuple of (area_id, area_name) or None
        assigned_areas: List of assigned Smart Heating area IDs

    Returns:
        Device information dictionary
    """
    ha_area_id, ha_area_name = ha_area if ha_area else (None, None)

    return {
        "id": entity.entity_id,
        "name": state.attributes.get("friendly_name", entity.entity_id),
        "type": device_type,
        "subtype": subtype,
        "entity_id": entity.entity_id,
        "domain": entity.domain,
        "assigned_areas": assigned_areas,
        "ha_area_id": ha_area_id,
        "ha_area_name": ha_area_name,
        "state": state.state,
        "attributes": {
            "temperature": state.attributes.get("temperature"),
            "current_temperature": state.attributes.get("current_temperature"),
            "unit_of_measurement": state.attributes.get("unit_of_measurement"),
        },
    }
