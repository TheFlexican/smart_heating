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

# Sensor states
STATE_INITIALIZED: Final = "initialized"
STATE_HEATING: Final = "heating"
STATE_IDLE: Final = "idle"
STATE_OFF: Final = "off"

# Zone device types
DEVICE_TYPE_THERMOSTAT: Final = "thermostat"
DEVICE_TYPE_TEMPERATURE_SENSOR: Final = "temperature_sensor"
DEVICE_TYPE_OPENTHERM_GATEWAY: Final = "opentherm_gateway"
DEVICE_TYPE_VALVE: Final = "valve"

# Platforms
PLATFORMS: Final = ["sensor", "climate", "switch"]

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
ATTR_SCHEDULE_ID: Final = "schedule_id"
ATTR_TIME: Final = "time"
ATTR_DAYS: Final = "days"
ATTR_NIGHT_BOOST_ENABLED: Final = "night_boost_enabled"
ATTR_NIGHT_BOOST_OFFSET: Final = "night_boost_offset"
ATTR_HYSTERESIS: Final = "hysteresis"
