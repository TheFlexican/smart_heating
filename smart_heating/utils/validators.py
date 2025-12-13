"""Validation utilities for API request data."""

from typing import Any, Dict, Optional, Tuple


def validate_temperature(
    temp: Any, min_temp: float = 5.0, max_temp: float = 35.0
) -> Tuple[bool, Optional[str]]:
    """Validate temperature value.

    Args:
        temp: Temperature value to validate
        min_temp: Minimum allowed temperature
        max_temp: Maximum allowed temperature

    Returns:
        Tuple of (is_valid, error_message)
    """
    if temp is None:
        return False, "Temperature is required"

    try:
        temp_float = float(temp)
    except (ValueError, TypeError):
        return False, "Temperature must be a number"

    if temp_float < min_temp or temp_float > max_temp:
        return False, f"Temperature must be between {min_temp}°C and {max_temp}°C"

    return True, None


def _validate_time_format(time_str: str) -> Tuple[bool, Optional[str]]:
    """Validate time string in HH:MM format.

    Args:
        time_str: Time string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(time_str, str) or ":" not in time_str:
        return False, "time must be in HH:MM format"

    try:
        hours, minutes = time_str.split(":")
        hours_int = int(hours)
        minutes_int = int(minutes)

        if hours_int < 0 or hours_int > 23:
            return False, "hours must be between 0 and 23"
        if minutes_int < 0 or minutes_int > 59:
            return False, "minutes must be between 0 and 59"
    except (ValueError, AttributeError):
        return False, "invalid time format"

    return True, None


def _validate_days_list(days: Any) -> Tuple[bool, Optional[str]]:
    """Validate days list.

    Args:
        days: List of days to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(days, list) or len(days) == 0:
        return False, "days must be a non-empty list"

    # Expect numeric day indices 0..6 (Monday=0)
    for day in days:
        if not isinstance(day, int):
            return False, f"invalid day: {day}. Days must be integer indices 0 (Monday) - 6 (Sunday)"
        if day < 0 or day > 6:
            return False, f"invalid day index: {day}. Must be between 0 and 6"

    return True, None


def validate_schedule_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate schedule entry data.

    Args:
        data: Schedule data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if "time" not in data:
        return False, "time is required"

    if "temperature" not in data:
        return False, "temperature is required"

    if "days" not in data:
        return False, "days is required"

    # Validate time format (HH:MM)
    is_valid, error_msg = _validate_time_format(data["time"])
    if not is_valid:
        return False, error_msg

    # Validate temperature
    is_valid, error_msg = validate_temperature(data["temperature"])
    if not is_valid:
        return False, error_msg

    # Validate days
    is_valid, error_msg = _validate_days_list(data["days"])
    if not is_valid:
        return False, error_msg

    return True, None


def validate_area_id(area_id: str) -> Tuple[bool, Optional[str]]:
    """Validate area ID.

    Args:
        area_id: Area identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not area_id:
        return False, "area_id is required"

    if not isinstance(area_id, str):
        return False, "area_id must be a string"

    return True, None


def validate_entity_id(entity_id: str) -> Tuple[bool, Optional[str]]:
    """Validate entity ID format.

    Args:
        entity_id: Entity identifier

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not entity_id:
        return False, "entity_id is required"

    if not isinstance(entity_id, str):
        return False, "entity_id must be a string"

    if "." not in entity_id:
        return False, "entity_id must be in format domain.object_id"

    return True, None
