export interface Device {
  id: string
  type: 'thermostat' | 'temperature_sensor' | 'opentherm_gateway' | 'valve'
  mqtt_topic?: string
  name?: string
  state?: string
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
  state: 'heating' | 'idle' | 'off'
  target_temperature: number
  current_temperature?: number
  devices: Device[]
  schedules?: ScheduleEntry[]
  night_boost_enabled?: boolean
  night_boost_offset?: number
  night_boost_start_time?: string
  night_boost_end_time?: string
  smart_night_boost_enabled?: boolean
  smart_night_boost_target_time?: string
  weather_entity_id?: string
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
