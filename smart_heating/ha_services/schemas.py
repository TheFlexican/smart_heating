"""Service schemas for Smart Heating."""

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from ..const import (
    ATTR_AREA_ID,
    ATTR_DEVICE_ID,
    ATTR_DEVICE_TYPE,
    ATTR_TEMPERATURE,
    ATTR_SCHEDULE_ID,
    ATTR_TIME,
    ATTR_DAYS,
    ATTR_NIGHT_BOOST_ENABLED,
    ATTR_NIGHT_BOOST_OFFSET,
    ATTR_NIGHT_BOOST_START_TIME,
    ATTR_NIGHT_BOOST_END_TIME,
    ATTR_HYSTERESIS,
    ATTR_PRESET_MODE,
    ATTR_BOOST_DURATION,
    ATTR_BOOST_TEMP,
    ATTR_FROST_PROTECTION_ENABLED,
    ATTR_FROST_PROTECTION_TEMP,
    ATTR_HVAC_MODE,
    ATTR_HISTORY_RETENTION_DAYS,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_TEMPERATURE_SENSOR,
    DEVICE_TYPE_OPENTHERM_GATEWAY,
    DEVICE_TYPE_VALVE,
    DEVICE_TYPE_SWITCH,
    PRESET_MODES,
    HVAC_MODES,
)

ADD_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_DEVICE_ID): cv.string,
    vol.Required(ATTR_DEVICE_TYPE): vol.In([
        DEVICE_TYPE_THERMOSTAT,
        DEVICE_TYPE_TEMPERATURE_SENSOR,
        DEVICE_TYPE_OPENTHERM_GATEWAY,
        DEVICE_TYPE_VALVE,
        DEVICE_TYPE_SWITCH,
    ]),
})

REMOVE_DEVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_DEVICE_ID): cv.string,
})

SET_TEMPERATURE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
})

ZONE_ID_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
})

ADD_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_SCHEDULE_ID): cv.string,
    vol.Required(ATTR_TIME): cv.string,
    vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
    vol.Optional(ATTR_DAYS): vol.All(cv.ensure_list, [cv.string]),
})

REMOVE_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_SCHEDULE_ID): cv.string,
})

SCHEDULE_CONTROL_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_SCHEDULE_ID): cv.string,
})

NIGHT_BOOST_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Optional(ATTR_NIGHT_BOOST_ENABLED): cv.boolean,
    vol.Optional(ATTR_NIGHT_BOOST_OFFSET): vol.Coerce(float),
    vol.Optional(ATTR_NIGHT_BOOST_START_TIME): cv.string,
    vol.Optional(ATTR_NIGHT_BOOST_END_TIME): cv.string,
    vol.Optional("smart_night_boost_enabled"): cv.boolean,
    vol.Optional("smart_night_boost_target_time"): cv.string,
    vol.Optional("weather_entity_id"): cv.string,
})

HYSTERESIS_SCHEMA = vol.Schema({
    vol.Required(ATTR_HYSTERESIS): vol.Coerce(float),
})

OPENTHERM_GATEWAY_SCHEMA = vol.Schema({
    vol.Optional("gateway_id"): cv.string,
    vol.Optional("enabled", default=True): cv.boolean,
})

TRV_TEMPERATURES_SCHEMA = vol.Schema({
    vol.Optional("heating_temp", default=25.0): vol.Coerce(float),
    vol.Optional("idle_temp", default=10.0): vol.Coerce(float),
    vol.Optional("temp_offset"): vol.Coerce(float),
})

PRESET_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_PRESET_MODE): vol.In(PRESET_MODES),
})

BOOST_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Optional(ATTR_BOOST_DURATION, default=60): vol.Coerce(int),
    vol.Optional(ATTR_BOOST_TEMP): vol.Coerce(float),
})

CANCEL_BOOST_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
})

FROST_PROTECTION_SCHEMA = vol.Schema({
    vol.Optional(ATTR_FROST_PROTECTION_ENABLED): cv.boolean,
    vol.Optional(ATTR_FROST_PROTECTION_TEMP): vol.Coerce(float),
})

WINDOW_SENSOR_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required("entity_id"): cv.entity_id,
})

PRESENCE_SENSOR_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required("entity_id"): cv.entity_id,
})

HVAC_MODE_SCHEMA = vol.Schema({
    vol.Required(ATTR_AREA_ID): cv.string,
    vol.Required(ATTR_HVAC_MODE): vol.In(HVAC_MODES),
})

COPY_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required("source_area_id"): cv.string,
    vol.Required("source_schedule_id"): cv.string,
    vol.Required("target_area_id"): cv.string,
    vol.Optional("target_days"): vol.All(cv.ensure_list, [cv.string]),
})

HISTORY_RETENTION_SCHEMA = vol.Schema({
    vol.Required(ATTR_HISTORY_RETENTION_DAYS): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
})

VACATION_MODE_SCHEMA = vol.Schema({
    vol.Optional("start_date"): cv.string,
    vol.Optional("end_date"): cv.string,
    vol.Optional("preset_mode", default="away"): vol.In(PRESET_MODES),
    vol.Optional("frost_protection_override", default=True): cv.boolean,
    vol.Optional("min_temperature", default=10.0): vol.Coerce(float),
    vol.Optional("auto_disable", default=True): cv.boolean,
})

SAFETY_SENSOR_SCHEMA = vol.Schema({
    vol.Required("sensor_id"): cv.string,
    vol.Optional("attribute", default="smoke"): cv.string,
    vol.Optional("alert_value", default=True): vol.Any(cv.boolean, cv.string),
    vol.Optional("enabled", default=True): cv.boolean,
})
