"""Constants for the Smart Heating integration."""

from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "smart_heating"

# Configuration and options
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_AREAS: Final = "areas"
CONF_MQTT_BASE_TOPIC: Final = "mqtt_base_topic"

# Default values
DEFAULT_UPDATE_INTERVAL: Final = 30  # seconds
DEFAULT_MQTT_BASE_TOPIC: Final = "zigbee2mqtt"

# Update interval
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)

# Services
SERVICE_REFRESH: Final = "refresh"
SERVICE_ADD_DEVICE_TO_AREA: Final = "add_device_to_area"
SERVICE_REMOVE_DEVICE_FROM_AREA: Final = "remove_device_from_area"
SERVICE_SET_AREA_TEMPERATURE: Final = "set_area_temperature"
SERVICE_ENABLE_AREA: Final = "enable_area"
SERVICE_DISABLE_AREA: Final = "disable_area"
SERVICE_ADD_SCHEDULE: Final = "add_schedule"
SERVICE_REMOVE_SCHEDULE: Final = "remove_schedule"
SERVICE_ENABLE_SCHEDULE: Final = "enable_schedule"
SERVICE_DISABLE_SCHEDULE: Final = "disable_schedule"
SERVICE_SET_NIGHT_BOOST: Final = "set_night_boost"
SERVICE_SET_HYSTERESIS: Final = "set_hysteresis"
SERVICE_SET_OPENTHERM_GATEWAY: Final = "set_opentherm_gateway"
SERVICE_SET_TRV_TEMPERATURES: Final = "set_trv_temperatures"
SERVICE_SET_PRESET_MODE: Final = "set_preset_mode"
SERVICE_SET_GLOBAL_PRESET_TEMP: Final = "set_global_preset_temperature"
SERVICE_SET_BOOST_MODE: Final = "set_boost_mode"
SERVICE_CANCEL_BOOST: Final = "cancel_boost"
SERVICE_SET_FROST_PROTECTION: Final = "set_frost_protection"
SERVICE_ADD_WINDOW_SENSOR: Final = "add_window_sensor"
SERVICE_REMOVE_WINDOW_SENSOR: Final = "remove_window_sensor"
SERVICE_ADD_PRESENCE_SENSOR: Final = "add_presence_sensor"
SERVICE_REMOVE_PRESENCE_SENSOR: Final = "remove_presence_sensor"
SERVICE_SET_HVAC_MODE: Final = "set_hvac_mode"
SERVICE_COPY_SCHEDULE: Final = "copy_schedule"
SERVICE_SET_HISTORY_RETENTION: Final = "set_history_retention"
SERVICE_ENABLE_VACATION_MODE: Final = "enable_vacation_mode"
SERVICE_DISABLE_VACATION_MODE: Final = "disable_vacation_mode"
SERVICE_SET_SAFETY_SENSOR: Final = "set_safety_sensor"
SERVICE_REMOVE_SAFETY_SENSOR: Final = "remove_safety_sensor"

# Sensor states
STATE_INITIALIZED: Final = "initialized"
STATE_HEATING: Final = "heating"
STATE_IDLE: Final = "idle"
STATE_OFF: Final = "off"

# Preset modes
PRESET_NONE: Final = "none"
PRESET_AWAY: Final = "away"
PRESET_ECO: Final = "eco"
PRESET_COMFORT: Final = "comfort"
PRESET_HOME: Final = "home"
PRESET_SLEEP: Final = "sleep"
PRESET_ACTIVITY: Final = "activity"
PRESET_BOOST: Final = "boost"

PRESET_MODES: Final = [
    PRESET_NONE,
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_COMFORT,
    PRESET_HOME,
    PRESET_SLEEP,
    PRESET_ACTIVITY,
    PRESET_BOOST,
]

# HVAC modes
HVAC_MODE_OFF: Final = "off"
HVAC_MODE_HEAT: Final = "heat"
HVAC_MODE_COOL: Final = "cool"
HVAC_MODE_HEAT_COOL: Final = "heat_cool"
HVAC_MODE_AUTO: Final = "auto"

# History settings
DEFAULT_HISTORY_RETENTION_DAYS: Final = 30  # Keep 30 days by default
HISTORY_RECORD_INTERVAL_SECONDS: Final = 300  # Record every 5 minutes

HVAC_MODES: Final = [
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
    HVAC_MODE_AUTO,
]

# Zone device types
DEVICE_TYPE_THERMOSTAT: Final = "thermostat"
DEVICE_TYPE_TEMPERATURE_SENSOR: Final = "temperature_sensor"
DEVICE_TYPE_OPENTHERM_GATEWAY: Final = "opentherm_gateway"
DEVICE_TYPE_VALVE: Final = "valve"
DEVICE_TYPE_SWITCH: Final = "switch"
DEVICE_TYPE_WINDOW_SENSOR: Final = "window_sensor"
DEVICE_TYPE_PRESENCE_SENSOR: Final = "presence_sensor"

# Platforms
PLATFORMS: Final = ["sensor", "switch"]

# Storage
STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_storage"

# Attributes
ATTR_AREA_ID: Final = "area_id"
ATTR_AREA_NAME: Final = "area_name"
ATTR_DEVICE_ID: Final = "device_id"
ATTR_DEVICE_TYPE: Final = "device_type"
ATTR_TEMPERATURE: Final = "temperature"
ATTR_TARGET_TEMPERATURE: Final = "target_temperature"
ATTR_CURRENT_TEMPERATURE: Final = "current_temperature"
ATTR_ENABLED: Final = "enabled"
ATTR_DEVICES: Final = "devices"

# Global OpenTherm Gateway
ATTR_OPENTHERM_GATEWAY: Final = "opentherm_gateway"
ATTR_OPENTHERM_ENABLED: Final = "opentherm_enabled"

# TRV Configuration
ATTR_TRV_HEATING_TEMP: Final = "trv_heating_temp"
ATTR_TRV_IDLE_TEMP: Final = "trv_idle_temp"
ATTR_TRV_TEMP_OFFSET: Final = "trv_temp_offset"
DEFAULT_TRV_HEATING_TEMP: Final = 25.0
DEFAULT_TRV_IDLE_TEMP: Final = 10.0
DEFAULT_TRV_TEMP_OFFSET: Final = 10.0  # Offset above target temp for temp-controlled valves
ATTR_SCHEDULE_ID: Final = "schedule_id"
ATTR_TIME: Final = "time"
ATTR_DAYS: Final = "days"
ATTR_NIGHT_BOOST_ENABLED: Final = "night_boost_enabled"
ATTR_NIGHT_BOOST_OFFSET: Final = "night_boost_offset"
ATTR_NIGHT_BOOST_START_TIME: Final = "night_boost_start_time"
ATTR_NIGHT_BOOST_END_TIME: Final = "night_boost_end_time"
ATTR_HYSTERESIS: Final = "hysteresis"

# Default night boost times
DEFAULT_NIGHT_BOOST_START_TIME: Final = "22:00"
DEFAULT_NIGHT_BOOST_END_TIME: Final = "06:00"

# Preset temperature attributes
ATTR_PRESET_MODE: Final = "preset_mode"
ATTR_AWAY_TEMP: Final = "away_temp"
ATTR_ECO_TEMP: Final = "eco_temp"
ATTR_COMFORT_TEMP: Final = "comfort_temp"
ATTR_HOME_TEMP: Final = "home_temp"
ATTR_SLEEP_TEMP: Final = "sleep_temp"
ATTR_ACTIVITY_TEMP: Final = "activity_temp"

# Preset configuration - per area choice between global or custom
ATTR_USE_GLOBAL_AWAY: Final = "use_global_away"
ATTR_USE_GLOBAL_ECO: Final = "use_global_eco"
ATTR_USE_GLOBAL_COMFORT: Final = "use_global_comfort"
ATTR_USE_GLOBAL_HOME: Final = "use_global_home"
ATTR_USE_GLOBAL_SLEEP: Final = "use_global_sleep"
ATTR_USE_GLOBAL_ACTIVITY: Final = "use_global_activity"

# Boost mode attributes
ATTR_BOOST_DURATION: Final = "boost_duration"
ATTR_BOOST_TEMP: Final = "boost_temp"
ATTR_BOOST_END_TIME: Final = "boost_end_time"

# Frost protection
ATTR_FROST_PROTECTION_ENABLED: Final = "frost_protection_enabled"
ATTR_FROST_PROTECTION_TEMP: Final = "frost_protection_temp"
DEFAULT_FROST_PROTECTION_TEMP: Final = 7.0

# Window sensor attributes
ATTR_WINDOW_OPEN_ACTION: Final = "window_open_action"
ATTR_WINDOW_OPEN_TEMP_DROP: Final = "window_open_temp_drop"
ATTR_ACTION_WHEN_OPEN: Final = "action_when_open"
DEFAULT_WINDOW_OPEN_TEMP_DROP: Final = 5.0

# Window sensor actions
WINDOW_ACTION_TURN_OFF: Final = "turn_off"
WINDOW_ACTION_REDUCE_TEMP: Final = "reduce_temperature"
WINDOW_ACTION_NONE: Final = "none"

# Presence sensor attributes
ATTR_PRESENCE_TEMP_BOOST: Final = "presence_temp_boost"
ATTR_ACTION_WHEN_AWAY: Final = "action_when_away"
ATTR_ACTION_WHEN_HOME: Final = "action_when_home"
ATTR_TEMP_DROP_WHEN_AWAY: Final = "temp_drop_when_away"
ATTR_TEMP_BOOST_WHEN_HOME: Final = "temp_boost_when_home"
DEFAULT_PRESENCE_TEMP_BOOST: Final = 2.0

# Presence sensor actions
PRESENCE_ACTION_TURN_OFF: Final = "turn_off"
PRESENCE_ACTION_REDUCE_TEMP: Final = "reduce_temperature"
PRESENCE_ACTION_SET_ECO: Final = "set_eco"
PRESENCE_ACTION_INCREASE_TEMP: Final = "increase_temperature"
PRESENCE_ACTION_SET_COMFORT: Final = "set_comfort"
PRESENCE_ACTION_NONE: Final = "none"

# HVAC mode
ATTR_HVAC_MODE: Final = "hvac_mode"
ATTR_AC_MODE: Final = "ac_mode"

# History settings
ATTR_HISTORY_RETENTION_DAYS: Final = "history_retention_days"
ATTR_HOURS: Final = "hours"
ATTR_START_TIME_PARAM: Final = "start_time"
ATTR_END_TIME_PARAM: Final = "end_time"
DEFAULT_HISTORY_RETENTION_DAYS: Final = 30  # Keep 30 days by default
HISTORY_RECORD_INTERVAL_SECONDS: Final = 300  # Record every 5 minutes

# Default preset temperatures
DEFAULT_AWAY_TEMP: Final = 16.0
DEFAULT_ECO_TEMP: Final = 18.0
DEFAULT_COMFORT_TEMP: Final = 22.0
DEFAULT_HOME_TEMP: Final = 20.0
DEFAULT_SLEEP_TEMP: Final = 18.5
DEFAULT_ACTIVITY_TEMP: Final = 21.0

# Safety sensor (smoke/CO) settings
ATTR_SAFETY_SENSOR_ID: Final = "safety_sensor_id"
ATTR_SAFETY_SENSOR_ATTRIBUTE: Final = "safety_sensor_attribute"
ATTR_SAFETY_SENSOR_ALERT_VALUE: Final = "safety_sensor_alert_value"
ATTR_SAFETY_SENSOR_ENABLED: Final = "safety_sensor_enabled"
SAFETY_SENSOR_TYPE_SMOKE: Final = "smoke"
SAFETY_SENSOR_TYPE_CO: Final = "carbon_monoxide"
SAFETY_SENSOR_TYPE_GAS: Final = "gas"
