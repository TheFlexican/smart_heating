export interface Device {
  id: string
  entity_id?: string  // Universal device ID (HA entity_id)
  type: 'thermostat' | 'temperature_sensor' | 'opentherm_gateway' | 'valve' | 'switch' | 'sensor' | 'number'
  subtype?: 'climate' | 'switch' | 'number' | 'temperature'  // Domain-based categorization (no keyword filtering)
  mqtt_topic?: string
  name?: string
  state?: string
  ha_area_id?: string
  area_id?: string  // Alias for ha_area_id for consistency
  ha_area_name?: string
  domain?: string  // HA domain (climate, sensor, switch, number)
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
  day?: string  // For weekly recurring schedules (legacy single day)
  days?: string[]  // For multi-day weekly recurring schedules
  date?: string  // For date-specific schedules (YYYY-MM-DD format)
  start_time: string
  end_time: string
  temperature?: number
  preset_mode?: string  // Optional: 'away', 'eco', 'comfort', 'home', 'sleep', 'activity'
}

export interface Zone {
  id: string
  name: string
  enabled: boolean
  hidden?: boolean
  state: 'heating' | 'idle' | 'off'
  target_temperature: number
  effective_target_temperature?: number  // Actual temperature considering presets, schedules, etc.
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
  weather_entity_id?: string | null

  // Preset mode settings
  preset_mode?: string
  away_temp?: number
  eco_temp?: number
  comfort_temp?: number
  home_temp?: number
  sleep_temp?: number
  activity_temp?: number

  // Global preset flags (use global vs custom temperatures)
  use_global_away?: boolean
  use_global_eco?: boolean
  use_global_comfort?: boolean
  use_global_home?: boolean
  use_global_sleep?: boolean
  use_global_activity?: boolean

  // Boost mode settings
  boost_mode_active?: boolean
  boost_duration?: number
  boost_temp?: number
  boost_end_time?: string

  // HVAC mode
  hvac_mode?: string

  // Manual override mode
  manual_override?: boolean

  // Switch/pump control setting
  shutdown_switches_when_idle?: boolean

  // Window sensor settings
  window_sensors?: WindowSensorConfig[]
  window_is_open?: boolean

  // Presence sensor settings
  presence_sensors?: PresenceSensorConfig[]
  presence_detected?: boolean
  use_global_presence?: boolean  // Use global presence sensors instead of area-specific

  // Auto preset mode based on presence
  auto_preset_enabled?: boolean
  auto_preset_home?: string  // Preset when presence detected (default: 'home')
  auto_preset_away?: string  // Preset when no presence (default: 'away')

  // Hysteresis override (null = use global setting)
  hysteresis_override?: number | null

  // Primary temperature sensor (which device to use for temperature measurement)
  primary_temperature_sensor?: string | null
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
  // Preset mode switching is automatic:
  // - Away when no presence → "away" preset
  // - Home when presence detected → "home" preset
}

// Safety sensor configuration
export interface SafetySensorConfig {
  sensor_id: string
  attribute: string
  alert_value: string | boolean
  enabled: boolean
}

// Home Assistant entity for selector
export interface HassEntity {
  entity_id: string
  name: string
  state: string
  attributes: {
    friendly_name?: string
    device_class?: string
    [key: string]: any
  }
}

// Alias Area to Zone for compatibility
export type Area = Zone

// Global preset temperatures
export interface GlobalPresets {
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}

// Global presence sensors
export interface GlobalPresence {
  sensors: PresenceSensorConfig[]
}

// Vacation mode configuration
export interface VacationMode {
  enabled: boolean
  start_date: string | null
  end_date: string | null
  preset_mode: string
  frost_protection_override: boolean
  min_temperature: number
  auto_disable: boolean
  person_entities: string[]
}

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

// User profile for multi-user presence tracking
export interface UserProfile {
  user_id: string  // Person entity ID
  name: string
  preset_preferences: {
    [preset: string]: number  // Preset name -> preferred temperature
  }
  priority: number  // 1-10, higher = more important
  areas: string[]  // Empty = all areas
}

export interface PresenceState {
  users_home: string[]  // List of user IDs currently home
  active_user: string | null  // Highest priority user currently home
  combined_mode: 'none' | 'single' | 'multiple'
}

export interface MultiUserSettings {
  multi_user_strategy: 'priority' | 'average'
  enabled: boolean
}

export interface UserData {
  users: { [user_id: string]: UserProfile }
  presence_state: PresenceState
  settings: MultiUserSettings
}

// Efficiency metrics for heating performance
export interface EfficiencyMetrics {
  energy_score: number  // 0-100 score
  heating_time_percentage: number  // % of time heating was active
  heating_cycles: number  // Number of on/off cycles
  avg_temp_delta: number  // Average difference from target temp
}

export interface EfficiencyReport {
  area_id?: string
  area_name?: string
  period: 'day' | 'week' | 'month' | 'year'
  start_date: string
  end_date: string
  metrics: EfficiencyMetrics
  recommendations: string[]
  summary_metrics?: EfficiencyMetrics  // For all-areas report
  area_reports?: EfficiencyReport[]  // For all-areas report
}

// Historical comparison types
export interface MetricDelta {
  change: number  // Absolute change
  percent_change: number  // Percentage change
  is_improvement: boolean  // Whether change is positive
}

export interface ComparisonResult {
  period: 'day' | 'week' | 'month' | 'year' | 'custom'
  current_start: string
  current_end: string
  previous_start: string
  previous_end: string
  current_summary: EfficiencyMetrics
  previous_summary: EfficiencyMetrics
  summary_delta?: {
    energy_score: MetricDelta
    heating_time: MetricDelta
    heating_cycles: MetricDelta
    temp_delta: MetricDelta
  }
  area_comparisons?: {
    area_id: string
    area_name: string
    current_metrics: EfficiencyMetrics
    previous_metrics: EfficiencyMetrics
    deltas: {
      energy_score: MetricDelta
      heating_time: MetricDelta
      heating_cycles: MetricDelta
      temp_delta: MetricDelta
    }
  }[]
}
