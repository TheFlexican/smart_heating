"""Coordinator data utilities for Smart Heating."""

import logging
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_coordinator(hass: HomeAssistant) -> Optional[Any]:
    """Get the Smart Heating coordinator instance.

    Args:
        hass: Home Assistant instance

    Returns:
        Coordinator instance or None
    """
    for _key, value in hass.data.get(DOMAIN, {}).items():
        if hasattr(value, "data") and hasattr(value, "async_request_refresh"):
            return value
    return None


def get_coordinator_devices(hass: HomeAssistant, area_id: str) -> Dict[str, Any]:
    """Get coordinator device data for an area.

    Args:
        hass: Home Assistant instance
        area_id: Area identifier

    Returns:
        Dictionary mapping device_id -> device_data
    """
    coordinator = get_coordinator(hass)
    if not coordinator or not coordinator.data:
        return {}

    areas_data = coordinator.data.get("areas", {})
    area_data = areas_data.get(area_id, {})

    device_dict = {}
    for device in area_data.get("devices", []):
        device_dict[device["id"]] = device

    return device_dict


def safe_coordinator_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove learning_engine from coordinator data before returning to API.

    The learning_engine contains circular references and is too large for JSON.

    Args:
        data: Coordinator data dictionary

    Returns:
        Filtered data dictionary
    """
    return {k: v for k, v in data.items() if k != "learning_engine"}
