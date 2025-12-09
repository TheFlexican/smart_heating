import axios from 'axios'
import { Area, Device, DeviceAdd, ScheduleEntry, LearningStats, HassEntity, WindowSensorConfig, PresenceSensorConfig, VacationMode, UserProfile, UserData, PresenceState, MultiUserSettings, EfficiencyReport, ComparisonResult } from './types'

const API_BASE = '/api/smart_heating'

export const getZones = async (): Promise<Area[]> => {
  const response = await axios.get(`${API_BASE}/areas`)
  return response.data.areas
}

export const getZone = async (areaId: string): Promise<Area> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}`)
  return response.data
}

export const addDeviceToZone = async (
  areaId: string,
  device: DeviceAdd
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/devices`, device)
}

export const removeDeviceFromZone = async (
  areaId: string,
  deviceId: string
): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/devices/${deviceId}`)
}

export const setZoneTemperature = async (
  areaId: string,
  temperature: number
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/temperature`, { temperature })
}

export const enableZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/enable`)
}

export const disableZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/disable`)
}

export const hideZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/hide`)
}

export const unhideZone = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/unhide`)
}

export const getDevices = async (): Promise<Device[]> => {
  const response = await axios.get(`${API_BASE}/devices`)
  return response.data.devices
}

export const refreshDevices = async (): Promise<{success: boolean, updated: number, available: number, message: string}> => {
  const response = await axios.get(`${API_BASE}/devices/refresh`)
  return response.data
}

export const getStatus = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/status`)
  return response.data
}

export const getConfig = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/config`)
  return response.data
}

export const getEntityState = async (entityId: string): Promise<any> => {
  const response = await axios.get(`${API_BASE}/entity_state/${entityId}`)
  return response.data
}

export const addScheduleToZone = async (
  areaId: string,
  schedule: Omit<ScheduleEntry, 'id'>
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/schedules`, schedule)
}

export const removeScheduleFromZone = async (
  areaId: string,
  scheduleId: string
): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/schedules/${scheduleId}`)
}

export const getLearningStats = async (areaId: string): Promise<LearningStats> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}/learning`)
  return response.data.stats
}

// ========== v0.3.0 API Functions ==========

// Preset Modes
export const setPresetMode = async (
  areaId: string,
  presetMode: string
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_mode`, { preset_mode: presetMode })
}

// Boost Mode
export const setBoostMode = async (
  areaId: string,
  duration: number,
  temperature?: number
): Promise<void> => {
  const data: any = { duration }
  if (temperature !== undefined) {
    data.temperature = temperature
  }
  await axios.post(`${API_BASE}/areas/${areaId}/boost`, data)
}

export const cancelBoost = async (areaId: string): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/cancel_boost`)
}

// Frost Protection (global)
export const setFrostProtection = async (
  enabled: boolean,
  temperature: number
): Promise<void> => {
  await axios.post(`${API_BASE}/frost_protection`, {
    enabled,
    temperature
  })
}

// Window Sensors
export const getBinarySensorEntities = async (): Promise<HassEntity[]> => {
  const response = await axios.get(`${API_BASE}/entities/binary_sensor`)
  return response.data.entities
}

export const getWeatherEntities = async (): Promise<HassEntity[]> => {
  const response = await axios.get(`${API_BASE}/entities/weather`)
  return response.data.entities
}

export const addWindowSensor = async (
  areaId: string,
  config: WindowSensorConfig
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/window_sensors`, config)
}

export const removeWindowSensor = async (
  areaId: string,
  sensorEntityId: string
): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/window_sensors/${sensorEntityId}`)
}

// Presence Sensors
export const addPresenceSensor = async (
  areaId: string,
  config: PresenceSensorConfig
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/presence_sensors`, config)
}

export const removePresenceSensor = async (
  areaId: string,
  sensorEntityId: string
): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}/presence_sensors/${sensorEntityId}`)
}

// HVAC Mode
export const setHvacMode = async (
  areaId: string,
  hvacMode: string
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/hvac_mode`, {
    hvac_mode: hvacMode
  })
}

// Switch/Pump Shutdown Control
export const setSwitchShutdown = async (
  areaId: string,
  shutdown: boolean
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/switch_shutdown`, {
    shutdown
  })
}

// Schedule Copying
export const copySchedule = async (
  sourceAreaId: string,
  targetAreaId: string,
  sourceDays?: string[],
  targetDays?: string[]
): Promise<void> => {
  const data: any = {
    source_area_id: sourceAreaId,
    target_area_id: targetAreaId
  }
  if (sourceDays) {
    data.source_days = sourceDays
  }
  if (targetDays) {
    data.target_days = targetDays
  }
  await axios.post(`${API_BASE}/copy_schedule`, data)
}

// History Management
export const getHistoryConfig = async (): Promise<{
  retention_days: number
  storage_backend: string
  record_interval_seconds: number
  record_interval_minutes: number
}> => {
  const response = await axios.get(`${API_BASE}/history/config`)
  return response.data
}

export const setHistoryRetention = async (days: number): Promise<void> => {
  await axios.post(`${API_BASE}/history/config`, {
    retention_days: days
  })
}

export const getHistoryStorageInfo = async (): Promise<{
  storage_backend: string
  retention_days: number
  database_enabled?: boolean
  database_stats?: {
    total_entries: number
    entries_by_area: Record<string, number>
    oldest_entry?: string
    newest_entry?: string
  }
}> => {
  const response = await axios.get(`${API_BASE}/history/storage/info`)
  return response.data
}

export const migrateHistoryStorage = async (targetBackend: 'json' | 'database'): Promise<{
  success: boolean
  message: string
  migrated_entries: number
  source_backend?: string
  target_backend?: string
}> => {
  const response = await axios.post(`${API_BASE}/history/storage/migrate`, {
    target_backend: targetBackend
  })
  return response.data
}

export const getDatabaseStats = async (): Promise<{
  enabled: boolean
  message?: string
  total_entries?: number
  entries_by_area?: Record<string, number>
  oldest_entry?: string
  newest_entry?: string
  table_name?: string
  backend?: string
}> => {
  const response = await axios.get(`${API_BASE}/history/storage/database/stats`)
  return response.data
}

export const cleanupHistory = async (): Promise<{ success: boolean }> => {
  const response = await axios.post(`${API_BASE}/history/cleanup`)
  return response.data
}

export const getHistory = async (
  areaId: string,
  options?: {
    hours?: number
    startTime?: string
    endTime?: string
  }
): Promise<{
  area_id: string
  hours?: number
  start_time?: string
  end_time?: string
  entries: Array<{
    timestamp: string
    current_temperature: number
    target_temperature: number
    state: string
  }>
  count: number
}> => {
  const params = new URLSearchParams()
  if (options?.hours) {
    params.append('hours', options.hours.toString())
  }
  if (options?.startTime) {
    params.append('start_time', options.startTime)
  }
  if (options?.endTime) {
    params.append('end_time', options.endTime)
  }

  const response = await axios.get(`${API_BASE}/areas/${areaId}/history?${params.toString()}`)
  return response.data
}

// Global preset temperature management
export const getGlobalPresets = async (): Promise<{
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}> => {
  const response = await axios.get(`${API_BASE}/global_presets`)
  return response.data
}

export const setGlobalPresets = async (presets: Partial<{
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}>): Promise<void> => {
  await axios.post(`${API_BASE}/global_presets`, presets)
}

export const setHideDevicesPanel = async (hide: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/hide_devices_panel`, { hide_devices_panel: hide })
}

export const setAreaPresetConfig = async (
  areaId: string,
  config: Partial<{
    use_global_away: boolean
    use_global_eco: boolean
    use_global_comfort: boolean
    use_global_home: boolean
    use_global_sleep: boolean
    use_global_activity: boolean
    away_temp: number
    eco_temp: number
    comfort_temp: number
    home_temp: number
    sleep_temp: number
    activity_temp: number
  }>
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_config`, config)
}

export const setManualOverride = async (
  areaId: string,
  enabled: boolean
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/manual_override`, { enabled })
}

export const setPrimaryTemperatureSensor = async (
  areaId: string,
  sensorId: string | null
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/primary_temp_sensor`, { sensor_id: sensorId })
}

// Global presence sensor management
export const getGlobalPresence = async (): Promise<{
  sensors: PresenceSensorConfig[]
}> => {
  const response = await axios.get(`${API_BASE}/global_presence`)
  return response.data
}

export const setGlobalPresence = async (sensors: PresenceSensorConfig[]): Promise<void> => {
  await axios.post(`${API_BASE}/global_presence`, { sensors })
}

export const setAreaPresenceConfig = async (
  areaId: string,
  useGlobal: boolean
): Promise<void> => {
  await axios.post(`${API_BASE}/areas/${areaId}/preset_config`, { use_global_presence: useGlobal })
}

// Vacation mode
export const getVacationMode = async (): Promise<VacationMode> => {
  const response = await axios.get(`${API_BASE}/vacation_mode`)
  return response.data
}

export const enableVacationMode = async (config: {
  start_date?: string
  end_date?: string
  preset_mode?: string
  frost_protection_override?: boolean
  min_temperature?: number
  auto_disable?: boolean
  person_entities?: string[]
}): Promise<VacationMode> => {
  const response = await axios.post(`${API_BASE}/vacation_mode`, config)
  return response.data
}

export const disableVacationMode = async (): Promise<VacationMode> => {
  const response = await axios.delete(`${API_BASE}/vacation_mode`)
  return response.data
}

// Area logging
export interface AreaLogEntry {
  timestamp: string
  type: string
  message: string
  details: Record<string, any>
}

export const getAreaLogs = async (
  areaId: string,
  options?: {
    limit?: number
    type?: string
  }
): Promise<AreaLogEntry[]> => {
  const params = new URLSearchParams()
  if (options?.limit) {
    params.append('limit', options.limit.toString())
  }
  if (options?.type) {
    params.append('type', options.type)
  }

  const response = await axios.get(`${API_BASE}/areas/${areaId}/logs?${params.toString()}`)
  return response.data.logs
}

// Hysteresis settings
export const getHysteresis = async (): Promise<number> => {
  const response = await axios.get(`${API_BASE}/hysteresis`)
  return response.data.hysteresis
}

export const setHysteresis = async (hysteresis: number): Promise<void> => {
  await axios.post(`${API_BASE}/hysteresis`, { hysteresis })
}

// Safety sensor settings
export interface SafetySensor {
  sensor_id: string
  attribute: string
  alert_value: string | boolean
  enabled: boolean
}

export interface SafetySensorResponse {
  sensors: SafetySensor[]
  alert_active?: boolean
}

export const getSafetySensor = async (): Promise<SafetySensorResponse> => {
  const response = await axios.get(`${API_BASE}/safety_sensor`)
  return response.data
}

export const setSafetySensor = async (config: {
  sensor_id: string
  attribute?: string
  alert_value?: string | boolean
  enabled?: boolean
}): Promise<void> => {
  await axios.post(`${API_BASE}/safety_sensor`, config)
}

export const removeSafetySensor = async (sensorId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/safety_sensor?sensor_id=${encodeURIComponent(sensorId)}`)
}

// Import/Export Configuration
export const exportConfig = async (): Promise<Blob> => {
  const response = await axios.get(`${API_BASE}/export`, {
    responseType: 'blob'
  })
  return response.data
}

export const importConfig = async (configData: any): Promise<{
  success: boolean
  message: string
  changes?: {
    areas_created: number
    areas_updated: number
    areas_deleted: number
    global_settings_updated: boolean
    vacation_mode_updated: boolean
  }
  error?: string
}> => {
  const response = await axios.post(`${API_BASE}/import`, configData)
  return response.data
}

export const validateConfig = async (configData: any): Promise<{
  valid: boolean
  version?: string
  export_date?: string
  areas_to_create?: number
  areas_to_update?: number
  global_settings_included?: boolean
  vacation_mode_included?: boolean
  error?: string
}> => {
  const response = await axios.post(`${API_BASE}/validate`, configData)
  return response.data
}

export const listBackups = async (): Promise<{
  backups: Array<{
    filename: string
    size: number
    created: number
  }>
}> => {
  const response = await axios.get(`${API_BASE}/backups`)
  return response.data
}

export const restoreBackup = async (filename: string): Promise<{
  success: boolean
  message: string
  changes?: any
  error?: string
}> => {
  const response = await axios.post(`${API_BASE}/backups/${filename}/restore`)
  return response.data
}

// ========== User Management (Multi-User Presence Tracking) ==========

export const getUsers = async (): Promise<UserData> => {
  const response = await axios.get(`${API_BASE}/users`)
  return response.data
}

export const getUser = async (userId: string): Promise<{ user: UserProfile }> => {
  const response = await axios.get(`${API_BASE}/users/${userId}`)
  return response.data
}

export const createUser = async (user: {
  user_id: string
  name: string
  person_entity: string
  preset_preferences?: { [preset: string]: number }
  priority?: number
  areas?: string[]
}): Promise<{ user: UserProfile }> => {
  const response = await axios.post(`${API_BASE}/users`, user)
  return response.data
}

export const updateUser = async (
  userId: string,
  updates: Partial<Omit<UserProfile, 'user_id'>>
): Promise<{ user: UserProfile }> => {
  const response = await axios.post(`${API_BASE}/users/${userId}`, updates)
  return response.data
}

export const deleteUser = async (userId: string): Promise<{ message: string }> => {
  const response = await axios.delete(`${API_BASE}/users/${userId}`)
  return response.data
}

export const updateUserSettings = async (settings: Partial<MultiUserSettings>): Promise<{ settings: MultiUserSettings }> => {
  const response = await axios.post(`${API_BASE}/users/settings`, settings)
  return response.data
}

export const getPresenceState = async (): Promise<{ presence_state: PresenceState }> => {
  const response = await axios.get(`${API_BASE}/users/presence`)
  return response.data
}

export const getActivePreferences = async (areaId?: string): Promise<{
  active_user_preferences: { [preset: string]: number } | null
  combined_preferences: { [preset: string]: number } | null
}> => {
  const url = areaId
    ? `${API_BASE}/users/preferences?area_id=${encodeURIComponent(areaId)}`
    : `${API_BASE}/users/preferences`
  const response = await axios.get(url)
  return response.data
}

// Efficiency Reports API
export const getEfficiencyReport = async (
  areaId: string,
  period: 'day' | 'week' | 'month' | 'year' = 'week'
): Promise<EfficiencyReport> => {
  const response = await axios.get(`${API_BASE}/efficiency/report/${areaId}?period=${period}`)
  return response.data
}

export const getAllAreasEfficiency = async (
  period: 'day' | 'week' | 'month' | 'year' = 'week'
): Promise<EfficiencyReport> => {
  const response = await axios.get(`${API_BASE}/efficiency/all_areas?period=${period}`)
  return response.data
}

export const getEfficiencyHistory = async (
  areaId: string,
  days: number = 30
): Promise<{ history: EfficiencyReport[] }> => {
  const response = await axios.get(`${API_BASE}/efficiency/history/${areaId}?days=${days}`)
  return response.data
}

// Historical Comparison API
export const getComparison = async (
  period: 'day' | 'week' | 'month' | 'year'
): Promise<ComparisonResult> => {
  const response = await axios.get(`${API_BASE}/comparison/${period}`)
  return response.data
}

export const getCustomComparison = async (
  startA: string,
  endA: string,
  startB: string,
  endB: string
): Promise<ComparisonResult> => {
  const response = await axios.post(`${API_BASE}/comparison/custom`, {
    start_a: startA,
    end_a: endA,
    start_b: startB,
    end_b: endB
  })
  return response.data
}

// OpenTherm Gateway Logging API
export const getOpenThermLogs = async (limit?: number): Promise<{
  logs: Array<{
    timestamp: string
    event_type: string
    data: any
    message?: string
  }>
  count: number
}> => {
  const params = limit ? `?limit=${limit}` : ''
  const response = await axios.get(`${API_BASE}/opentherm/logs${params}`)
  return response.data
}

export const getOpenThermCapabilities = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/opentherm/capabilities`)
  return response.data
}

export const discoverOpenThermCapabilities = async (): Promise<any> => {
  const response = await axios.post(`${API_BASE}/opentherm/capabilities/discover`)
  return response.data
}

export const clearOpenThermLogs = async (): Promise<{ success: boolean, message: string }> => {
  const response = await axios.post(`${API_BASE}/opentherm/logs/clear`)
  return response.data
}

export const setOpenthermGateway = async (gatewayId: string, enabled: boolean): Promise<void> => {
  await axios.post(`${API_BASE}/opentherm_gateway`, {
    gateway_id: gatewayId,
    enabled: enabled
  })
}

export const getOpenThermSensorStates = async (): Promise<{
  control_setpoint?: number
  modulation_level?: number
  ch_water_temp?: number
  flow_temp?: number
  room_temp?: number
  room_setpoint?: number
  boiler_status?: string
  flame_on?: boolean
}> => {
  // Get multiple sensor states in parallel
  const sensorIds = [
    'sensor.opentherm_ketel_regel_instelpunt_1',
    'sensor.opentherm_ketel_modulatie_niveau',
    'sensor.opentherm_ketel_cv_watertemperatuur',
    'sensor.opentherm_ketel_aanvoertemperatuur',
    'sensor.opentherm_thermostaat_kamertemperatuur',
    'sensor.opentherm_thermostaat_kamer_instelpunt',
    'binary_sensor.opentherm_ketel_vlam_status',
  ]

  const results = await Promise.allSettled(
    sensorIds.map(id => getEntityState(id).catch(() => null))
  )

  const states: any = {}

  results.forEach((result, index) => {
    if (result.status === 'fulfilled' && result.value) {
      const sensorId = sensorIds[index]
      const value = result.value.state

      if (sensorId.includes('regel_instelpunt')) {
        states.control_setpoint = parseFloat(value)
      } else if (sensorId.includes('modulatie')) {
        states.modulation_level = parseFloat(value)
      } else if (sensorId.includes('cv_water')) {
        states.ch_water_temp = parseFloat(value)
      } else if (sensorId.includes('aanvoer')) {
        states.flow_temp = parseFloat(value)
      } else if (sensorId.includes('kamertemperatuur')) {
        states.room_temp = parseFloat(value)
      } else if (sensorId.includes('kamer_instelpunt')) {
        states.room_setpoint = parseFloat(value)
      } else if (sensorId.includes('vlam')) {
        states.flame_on = value === 'on'
      }
    }
  })

  return states
}
