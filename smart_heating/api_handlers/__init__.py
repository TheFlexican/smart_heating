"""API handlers for Smart Heating."""

from .areas import (
    handle_disable_area,
    handle_enable_area,
    handle_get_area,
    handle_get_areas,
    handle_hide_area,
    handle_set_area_hysteresis,
    handle_set_area_preset_config,
    handle_set_auto_preset,
    handle_set_heating_type,
    handle_set_area_heating_curve,
    handle_set_manual_override,
    handle_set_primary_temperature_sensor,
    handle_set_switch_shutdown,
    handle_set_temperature,
    handle_unhide_area,
)
from .config import (
    handle_disable_vacation_mode,
    handle_enable_vacation_mode,
    handle_get_config,
    handle_get_global_presence,
    handle_get_global_presets,
    handle_get_hysteresis,
    handle_get_safety_sensor,
    handle_get_vacation_mode,
    handle_remove_safety_sensor,
    handle_set_frost_protection,
    handle_set_global_presence,
    handle_set_global_presets,
    handle_set_hide_devices_panel,
    handle_set_hvac_mode,
    handle_set_hysteresis_value,
    handle_set_opentherm_gateway,
    handle_set_safety_sensor,
    handle_set_advanced_control_config,
)
from .comparison import (
    handle_get_comparison,
    handle_get_custom_comparison,
)
from .devices import (
    handle_add_device,
    handle_get_devices,
    handle_refresh_devices,
    handle_remove_device,
)
from .efficiency import (
    handle_get_area_efficiency_history,
    handle_get_efficiency_report,
)
from .history import (
    handle_cleanup_history,
    handle_get_database_stats,
    handle_get_history,
    handle_get_history_config,
    handle_get_history_storage_info,
    handle_get_learning_stats,
    handle_migrate_history_storage,
    handle_set_history_config,
)
from .import_export import (
    handle_export_config,
    handle_import_config,
    handle_list_backups,
    handle_restore_backup,
    handle_validate_config,
)
from .logs import (
    handle_get_area_logs,
)
from .opentherm import (
    handle_clear_opentherm_logs,
    handle_discover_opentherm_capabilities,
    handle_get_opentherm_logs,
    handle_get_opentherm_gateways,
    handle_calibrate_opentherm,
)
from .schedules import (
    handle_add_schedule,
    handle_cancel_boost,
    handle_remove_schedule,
    handle_update_schedule,
    handle_set_boost_mode,
    handle_set_preset_mode,
)
from .sensors import (
    handle_add_presence_sensor,
    handle_add_window_sensor,
    handle_get_binary_sensor_entities,
    handle_get_weather_entities,
    handle_remove_presence_sensor,
    handle_remove_window_sensor,
)
from .system import (
    handle_call_service,
    handle_get_entity_state,
    handle_get_status,
)
from .users import (
    handle_create_user,
    handle_delete_user,
    handle_get_active_preferences,
    handle_get_presence_state,
    handle_get_user,
    handle_get_users,
    handle_update_user,
    handle_update_user_settings,
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
    "handle_set_heating_type",
    "handle_set_auto_preset",
    "handle_set_area_preset_config",
    "handle_set_manual_override",
    "handle_set_area_heating_curve",
    # Devices
    "handle_get_devices",
    "handle_refresh_devices",
    "handle_add_device",
    "handle_remove_device",
    # Efficiency
    "handle_get_efficiency_report",
    "handle_get_area_efficiency_history",
    # Schedules
    "handle_add_schedule",
    "handle_remove_schedule",
    "handle_update_schedule",
    "handle_set_preset_mode",
    "handle_set_boost_mode",
    "handle_cancel_boost",
    # Sensors
    "handle_add_window_sensor",
    "handle_remove_window_sensor",
    "handle_add_presence_sensor",
    "handle_remove_presence_sensor",
    "handle_get_binary_sensor_entities",
    "handle_get_weather_entities",
    # Config
    "handle_get_config",
    "handle_get_global_presets",
    "handle_set_global_presets",
    "handle_get_hysteresis",
    "handle_set_hysteresis_value",
    "handle_set_opentherm_gateway",
    "handle_get_global_presence",
    "handle_set_global_presence",
    "handle_set_hide_devices_panel",
    "handle_set_frost_protection",
    "handle_get_vacation_mode",
    "handle_enable_vacation_mode",
    "handle_disable_vacation_mode",
    "handle_get_safety_sensor",
    "handle_set_safety_sensor",
    "handle_remove_safety_sensor",
    "handle_set_hvac_mode",
    "handle_set_advanced_control_config",
    # Comparison
    "handle_get_comparison",
    "handle_get_custom_comparison",
    # History
    "handle_get_history",
    "handle_get_learning_stats",
    "handle_get_history_config",
    "handle_set_history_config",
    "handle_get_history_storage_info",
    "handle_migrate_history_storage",
    "handle_get_database_stats",
    "handle_cleanup_history",
    # Import/Export
    "handle_export_config",
    "handle_import_config",
    "handle_validate_config",
    "handle_list_backups",
    "handle_restore_backup",
    # Logs
    "handle_get_area_logs",
    # OpenTherm
    "handle_get_opentherm_logs",
    "handle_discover_opentherm_capabilities",
    "handle_clear_opentherm_logs",
    "handle_get_opentherm_gateways",
    "handle_calibrate_opentherm",
    # System
    "handle_get_status",
    "handle_get_entity_state",
    "handle_call_service",
    "handle_set_primary_temperature_sensor",
    # Users
    "handle_get_users",
    "handle_get_user",
    "handle_create_user",
    "handle_update_user",
    "handle_delete_user",
    "handle_update_user_settings",
    "handle_get_presence_state",
    "handle_get_active_preferences",
]
