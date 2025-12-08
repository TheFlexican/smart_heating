"""Utility modules for Smart Heating."""

from .coordinator_helpers import (
    get_coordinator,
    get_coordinator_devices,
    safe_coordinator_data,
)
from .device_registry import DeviceRegistry, build_device_dict
from .response_builders import build_area_response, build_device_info
from .validators import (
    validate_area_id,
    validate_entity_id,
    validate_schedule_data,
    validate_temperature,
)

__all__ = [
    "build_area_response",
    "build_device_info",
    "validate_temperature",
    "validate_schedule_data",
    "validate_area_id",
    "validate_entity_id",
    "DeviceRegistry",
    "build_device_dict",
    "get_coordinator",
    "get_coordinator_devices",
    "safe_coordinator_data",
]
