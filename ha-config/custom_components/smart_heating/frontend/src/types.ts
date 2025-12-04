export interface Device {
  id: string
  type: 'thermostat' | 'temperature_sensor' | 'opentherm_gateway' | 'valve'
  mqtt_topic?: string
  name?: string
}

export interface Area {
  id: string
  name: string
  enabled: boolean
  state: 'heating' | 'idle' | 'off'
  target_temperature: number
  current_temperature?: number
  devices: Device[]
}

export interface AreaCreate {
  zone_id: string
  zone_name: string
  temperature?: number
}

export interface DeviceAdd {
  device_id: string
  device_type: string
  mqtt_topic?: string
}
