export interface Device {
  id: string
  type: 'thermostat' | 'temperature_sensor' | 'opentherm_gateway' | 'valve'
  mqtt_topic?: string
  name?: string
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
}

// Alias Area to Zone for compatibility
export type Area = Zone

export interface DeviceAdd {
  device_id: string
  device_type: string
  mqtt_topic?: string
}
