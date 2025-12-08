"""Home Assistant service handlers for Smart Heating."""

from .area_handlers import (
    async_handle_disable_area,
    async_handle_enable_area,
    async_handle_set_temperature,
)
from .config_handlers import (
    async_handle_set_frost_protection,
    async_handle_set_history_retention,
    async_handle_set_hysteresis,
    async_handle_set_opentherm_gateway,
    async_handle_set_trv_temperatures,
)
from .device_handlers import (
    async_handle_add_device,
    async_handle_remove_device,
)
from .hvac_handlers import (
    async_handle_cancel_boost,
    async_handle_set_boost_mode,
    async_handle_set_hvac_mode,
    async_handle_set_preset_mode,
)
from .safety_handlers import (
    async_handle_remove_safety_sensor,
    async_handle_set_safety_sensor,
)
from .schedule_handlers import (
    async_handle_add_schedule,
    async_handle_copy_schedule,
    async_handle_disable_schedule,
    async_handle_enable_schedule,
    async_handle_remove_schedule,
    async_handle_set_night_boost,
)
from .schemas import (
    ADD_DEVICE_SCHEMA,
    ADD_SCHEDULE_SCHEMA,
    BOOST_MODE_SCHEMA,
    CANCEL_BOOST_SCHEMA,
    COPY_SCHEDULE_SCHEMA,
    FROST_PROTECTION_SCHEMA,
    HISTORY_RETENTION_SCHEMA,
    HVAC_MODE_SCHEMA,
    HYSTERESIS_SCHEMA,
    NIGHT_BOOST_SCHEMA,
    OPENTHERM_GATEWAY_SCHEMA,
    PRESENCE_SENSOR_SCHEMA,
    PRESET_MODE_SCHEMA,
    REMOVE_DEVICE_SCHEMA,
    REMOVE_SCHEDULE_SCHEMA,
    SAFETY_SENSOR_SCHEMA,
    SCHEDULE_CONTROL_SCHEMA,
    SET_TEMPERATURE_SCHEMA,
    TRV_TEMPERATURES_SCHEMA,
    VACATION_MODE_SCHEMA,
    WINDOW_SENSOR_SCHEMA,
    ZONE_ID_SCHEMA,
)
from .sensor_handlers import (
    async_handle_add_presence_sensor,
    async_handle_add_window_sensor,
    async_handle_remove_presence_sensor,
    async_handle_remove_window_sensor,
)
from .system_handlers import (
    async_handle_refresh,
)
from .vacation_handlers import (
    async_handle_disable_vacation_mode,
    async_handle_enable_vacation_mode,
)

__all__ = [
    # Area handlers
    "async_handle_enable_area",
    "async_handle_disable_area",
    "async_handle_set_temperature",
    # Config handlers
    "async_handle_set_hysteresis",
    "async_handle_set_opentherm_gateway",
    "async_handle_set_trv_temperatures",
    "async_handle_set_frost_protection",
    "async_handle_set_history_retention",
    # Device handlers
    "async_handle_add_device",
    "async_handle_remove_device",
    # HVAC handlers
    "async_handle_set_preset_mode",
    "async_handle_set_boost_mode",
    "async_handle_cancel_boost",
    "async_handle_set_hvac_mode",
    # Safety handlers
    "async_handle_set_safety_sensor",
    "async_handle_remove_safety_sensor",
    # Schedule handlers
    "async_handle_add_schedule",
    "async_handle_remove_schedule",
    "async_handle_enable_schedule",
    "async_handle_disable_schedule",
    "async_handle_copy_schedule",
    "async_handle_set_night_boost",
    # Sensor handlers
    "async_handle_add_window_sensor",
    "async_handle_remove_window_sensor",
    "async_handle_add_presence_sensor",
    "async_handle_remove_presence_sensor",
    # System handlers
    "async_handle_refresh",
    # Vacation handlers
    "async_handle_enable_vacation_mode",
    "async_handle_disable_vacation_mode",
    # Schemas
    "ADD_DEVICE_SCHEMA",
    "REMOVE_DEVICE_SCHEMA",
    "SET_TEMPERATURE_SCHEMA",
    "ZONE_ID_SCHEMA",
    "ADD_SCHEDULE_SCHEMA",
    "REMOVE_SCHEDULE_SCHEMA",
    "SCHEDULE_CONTROL_SCHEMA",
    "NIGHT_BOOST_SCHEMA",
    "HYSTERESIS_SCHEMA",
    "OPENTHERM_GATEWAY_SCHEMA",
    "TRV_TEMPERATURES_SCHEMA",
    "PRESET_MODE_SCHEMA",
    "BOOST_MODE_SCHEMA",
    "CANCEL_BOOST_SCHEMA",
    "FROST_PROTECTION_SCHEMA",
    "WINDOW_SENSOR_SCHEMA",
    "PRESENCE_SENSOR_SCHEMA",
    "HVAC_MODE_SCHEMA",
    "COPY_SCHEDULE_SCHEMA",
    "HISTORY_RETENTION_SCHEMA",
    "VACATION_MODE_SCHEMA",
    "SAFETY_SENSOR_SCHEMA",
]
