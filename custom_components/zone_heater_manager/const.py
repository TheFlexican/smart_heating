"""Constants for the Zone Heater Manager integration."""
from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "zone_heater_manager"

# Configuration and options
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_ZONES: Final = "zones"
CONF_MQTT_BASE_TOPIC: Final = "mqtt_base_topic"

# Default values
DEFAULT_UPDATE_INTERVAL: Final = 30  # seconds
DEFAULT_MQTT_BASE_TOPIC: Final = "zigbee2mqtt"

# Update interval
UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)

# Services
SERVICE_REFRESH: Final = "refresh"
SERVICE_CREATE_ZONE: Final = "create_zone"
SERVICE_DELETE_ZONE: Final = "delete_zone"
SERVICE_ADD_DEVICE_TO_ZONE: Final = "add_device_to_zone"
SERVICE_REMOVE_DEVICE_FROM_ZONE: Final = "remove_device_from_zone"
SERVICE_SET_ZONE_TEMPERATURE: Final = "set_zone_temperature"
SERVICE_ENABLE_ZONE: Final = "enable_zone"
SERVICE_DISABLE_ZONE: Final = "disable_zone"

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
ATTR_ZONE_ID: Final = "zone_id"
ATTR_ZONE_NAME: Final = "zone_name"
ATTR_DEVICE_ID: Final = "device_id"
ATTR_DEVICE_TYPE: Final = "device_type"
ATTR_TEMPERATURE: Final = "temperature"
ATTR_TARGET_TEMPERATURE: Final = "target_temperature"
ATTR_CURRENT_TEMPERATURE: Final = "current_temperature"
ATTR_ENABLED: Final = "enabled"
ATTR_DEVICES: Final = "devices"
