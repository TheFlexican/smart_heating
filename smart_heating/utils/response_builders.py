"""Response builder utilities for API handlers."""

from typing import Any, Dict, List, Optional

from ..models.area import Area


def build_device_info(
    device_id: str,
    device_data: Dict[str, Any],
    state_obj: Any = None,
    coordinator_device: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build device information dictionary.

    Args:
        device_id: Device entity ID
        device_data: Stored device data
        state_obj: Home Assistant state object
        coordinator_device: Coordinator device data

    Returns:
        Device information dictionary
    """
    device_info = {
        "id": device_id,
        "type": device_data["type"],
        "mqtt_topic": device_data.get("mqtt_topic"),
    }

    # Add friendly name from entity state
    if state_obj:
        device_info["name"] = state_obj.attributes.get("friendly_name", device_id)

    # Add coordinator data if available
    if coordinator_device:
        device_info.update(
            {
                "state": coordinator_device.get("state"),
                "current_temperature": coordinator_device.get("current_temperature"),
                "target_temperature": coordinator_device.get("target_temperature"),
                "hvac_action": coordinator_device.get("hvac_action"),
                "temperature": coordinator_device.get("temperature"),
                "position": coordinator_device.get("position"),
            }
        )

    return device_info


def build_area_response(
    area: Area, devices_list: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Build area response dictionary.

    Args:
        area: Area model instance
        devices_list: Optional list of device information dictionaries

    Returns:
        Area data dictionary
    """
    if devices_list is None:
        devices_list = []

    return {
        "id": area.area_id,
        "name": area.name,
        "enabled": area.enabled,
        "hidden": area.hidden,
        "state": area.state,
        "target_temperature": area.target_temperature,
        "effective_target_temperature": area.get_effective_target_temperature(),
        "current_temperature": area.current_temperature,
        "devices": devices_list,
        "schedules": [s.to_dict() for s in area.schedules.values()],
        # Night boost
        "night_boost_enabled": area.night_boost_enabled,
        "night_boost_offset": area.night_boost_offset,
        "night_boost_start_time": area.night_boost_start_time,
        "night_boost_end_time": area.night_boost_end_time,
        # Smart night boost
        "smart_night_boost_enabled": area.smart_night_boost_enabled,
        "smart_night_boost_target_time": area.smart_night_boost_target_time,
        "weather_entity_id": area.weather_entity_id,
        # Preset modes
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
        # Boost mode
        "boost_mode_active": area.boost_mode_active,
        "boost_temp": area.boost_temp,
        "boost_duration": area.boost_duration,
        # HVAC mode
        "hvac_mode": area.hvac_mode,
        # Hysteresis override
        "hysteresis_override": area.hysteresis_override,
        # Manual override
        "manual_override": getattr(area, "manual_override", False),
        # Sensors
        "window_sensors": area.window_sensors,
        "presence_sensors": area.presence_sensors,
        "use_global_presence": area.use_global_presence,
        # Auto preset mode
        "auto_preset_enabled": getattr(area, "auto_preset_enabled", False),
        "auto_preset_home": getattr(area, "auto_preset_home", "home"),
        "auto_preset_away": getattr(area, "auto_preset_away", "away"),
        # Switch shutdown
        "switch_shutdown_enabled": getattr(area, "switch_shutdown_enabled", False),
        "switch_shutdown_entities": getattr(area, "switch_shutdown_entities", []),
        # Primary temperature sensor
        "primary_temperature_sensor": getattr(area, "primary_temperature_sensor", None),
    }
