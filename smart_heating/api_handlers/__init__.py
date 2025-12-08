"""API handlers for Smart Heating."""

from .areas import (
    handle_get_areas,
    handle_get_area,
    handle_set_temperature,
    handle_enable_area,
    handle_disable_area,
    handle_hide_area,
    handle_unhide_area,
    handle_set_switch_shutdown,
    handle_set_area_hysteresis,
    handle_set_auto_preset,
    handle_set_area_preset_config,
    handle_set_manual_override,
    handle_set_primary_temperature_sensor,
)

from .devices import (
    handle_get_devices,
    handle_refresh_devices,
    handle_add_device,
    handle_remove_device,
)

from .schedules import (
    handle_add_schedule,
    handle_remove_schedule,
    handle_set_preset_mode,
    handle_set_boost_mode,
    handle_cancel_boost,
)

from .sensors import (
    handle_add_window_sensor,
    handle_remove_window_sensor,
    handle_add_presence_sensor,
    handle_remove_presence_sensor,
    handle_get_binary_sensor_entities,
)

from .config import (
    handle_get_config,
    handle_get_global_presets,
    handle_set_global_presets,
    handle_get_hysteresis,
    handle_set_hysteresis_value,
    handle_get_global_presence,
    handle_set_global_presence,
    handle_set_frost_protection,
    handle_get_vacation_mode,
    handle_enable_vacation_mode,
    handle_disable_vacation_mode,
    handle_get_safety_sensor,
    handle_set_safety_sensor,
    handle_remove_safety_sensor,
    handle_set_hvac_mode,
)

from .history import (
    handle_get_history,
    handle_get_learning_stats,
    handle_get_history_config,
    handle_set_history_config,
)

from .logs import (
    handle_get_area_logs,
)

from .system import (
    handle_get_status,
    handle_get_entity_state,
    handle_call_service,
)

__all__ = [
    # Areas
    "handle_get_areas",
    "handle_get_area",
    "handle_set_temperature",
    "handle_enable_area",
    "handle_disable_area",
    "handle_hide_area",
    "handle_unhide_area",
    "handle_set_switch_shutdown",
    "handle_set_area_hysteresis",
    "handle_set_auto_preset",
    "handle_set_area_preset_config",
    "handle_set_manual_override",
    # Devices
    "handle_get_devices",
    "handle_refresh_devices",
    "handle_add_device",
    "handle_remove_device",
    # Schedules
    "handle_add_schedule",
    "handle_remove_schedule",
    "handle_set_preset_mode",
    "handle_set_boost_mode",
    "handle_cancel_boost",
    # Sensors
    "handle_add_window_sensor",
    "handle_remove_window_sensor",
    "handle_add_presence_sensor",
    "handle_remove_presence_sensor",
    "handle_get_binary_sensor_entities",
    # Config
    "handle_get_config",
    "handle_get_global_presets",
    "handle_set_global_presets",
    "handle_get_hysteresis",
    "handle_set_hysteresis_value",
    "handle_get_global_presence",
    "handle_set_global_presence",
    "handle_set_frost_protection",
    "handle_get_vacation_mode",
    "handle_enable_vacation_mode",
    "handle_disable_vacation_mode",
    "handle_get_safety_sensor",
    "handle_set_safety_sensor",
    "handle_remove_safety_sensor",
    "handle_set_hvac_mode",
    # History
    "handle_get_history",
    "handle_get_learning_stats",
    "handle_get_history_config",
    "handle_set_history_config",
    # Logs
    "handle_get_area_logs",
    # System
    "handle_get_status",
    "handle_get_entity_state",
    "handle_call_service",
]
