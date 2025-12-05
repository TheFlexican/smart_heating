export interface Device {
  id: string
  type: 'thermostat' | 'temperature_sensor' | 'opentherm_gateway' | 'valve'
  mqtt_topic?: string
  name?: string
  state?: string
  ha_area_id?: string
  ha_area_name?: string
  // Thermostat specific
  hvac_action?: string
  current_temperature?: number
  target_temperature?: number
  // Temperature sensor specific
  temperature?: number | string
  // Valve specific
  position?: number
}

export interface ScheduleEntry {
  id: string
  day: string
  start_time: string
  end_time: string
  temperature: number
}

export interface Zone {
  id: string
  name: string
  enabled: boolean
  hidden?: boolean
  state: 'heating' | 'idle' | 'off'
  target_temperature: number
  current_temperature?: number
  devices: Device[]
  schedules?: ScheduleEntry[]
  
  // Night boost settings
  night_boost_enabled?: boolean
  night_boost_offset?: number
  night_boost_start_time?: string
  night_boost_end_time?: string
  
  // Smart night boost settings
  smart_night_boost_enabled?: boolean
  smart_night_boost_target_time?: string
  weather_entity_id?: string
  
  // Preset mode settings
  preset_mode?: string
  away_temp?: number
  eco_temp?: number
  comfort_temp?: number
  home_temp?: number
  sleep_temp?: number
  activity_temp?: number
  
  // Boost mode settings
  boost_mode_active?: boolean
  boost_duration?: number
  boost_temp?: number
  boost_end_time?: string
  
  // HVAC mode
  hvac_mode?: string
  
  // Window sensor settings
  window_sensors?: WindowSensorConfig[]
  window_is_open?: boolean
  
  // Presence sensor settings
  presence_sensors?: PresenceSensorConfig[]
  presence_detected?: boolean
}

// Window sensor configuration
export interface WindowSensorConfig {
  entity_id: string
  action_when_open: 'turn_off' | 'reduce_temperature' | 'none'
  temp_drop?: number  // Only used when action_when_open is 'reduce_temperature'
}

// Presence sensor configuration
export interface PresenceSensorConfig {
  entity_id: string
  action_when_away: 'turn_off' | 'reduce_temperature' | 'set_eco' | 'none'
  action_when_home: 'increase_temperature' | 'set_comfort' | 'none'
  temp_drop_when_away?: number  // Only used when action_when_away is 'reduce_temperature'
  temp_boost_when_home?: number  // Only used when action_when_home is 'increase_temperature'
}

// Home Assistant entity for selector
export interface HassEntity {
  entity_id: string
  state: string
  attributes: {
    friendly_name?: string
    device_class?: string
    [key: string]: any
  }
}

// Alias Area to Zone for compatibility
export type Area = Zone

export interface LearningStats {
  total_events: number
  avg_heating_rate: number
  avg_outdoor_correlation: number
  prediction_accuracy: number
  last_updated?: string
}

export interface DeviceAdd {
  device_id: string
  device_type: string
  mqtt_topic?: string
}
