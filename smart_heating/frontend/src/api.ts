import axios from 'axios'
import { Area, Device, DeviceAdd, ScheduleEntry, LearningStats, HassEntity, WindowSensorConfig, PresenceSensorConfig, VacationMode } from './types'

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

export const setAreaPresetConfig = async (
  areaId: string,
  config: Partial<{
    use_global_away: boolean
    use_global_eco: boolean
    use_global_comfort: boolean
    use_global_home: boolean
    use_global_sleep: boolean
    use_global_activity: boolean
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
  await axios.post(`${API_BASE}/call_service`, {
    service: 'set_hysteresis',
    hysteresis
  })
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
