import axios from 'axios'
import { Zone, Device, ZoneCreate, DeviceAdd } from './types'

const API_BASE = '/api/zone_heater_manager'

export const getZones = async (): Promise<Zone[]> => {
  const response = await axios.get(`${API_BASE}/zones`)
  return response.data.zones
}

export const getZone = async (zoneId: string): Promise<Zone> => {
  const response = await axios.get(`${API_BASE}/zones/${zoneId}`)
  return response.data
}

export const createZone = async (data: ZoneCreate): Promise<Zone> => {
  const response = await axios.post(`${API_BASE}/zones`, data)
  return response.data.zone
}

export const deleteZone = async (zoneId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/zones/${zoneId}`)
}

export const addDeviceToZone = async (
  zoneId: string,
  device: DeviceAdd
): Promise<void> => {
  await axios.post(`${API_BASE}/zones/${zoneId}/devices`, device)
}

export const removeDeviceFromZone = async (
  zoneId: string,
  deviceId: string
): Promise<void> => {
  await axios.delete(`${API_BASE}/zones/${zoneId}/devices/${deviceId}`)
}

export const setZoneTemperature = async (
  zoneId: string,
  temperature: number
): Promise<void> => {
  await axios.post(`${API_BASE}/zones/${zoneId}/temperature`, { temperature })
}

export const enableZone = async (zoneId: string): Promise<void> => {
  await axios.post(`${API_BASE}/zones/${zoneId}/enable`)
}

export const disableZone = async (zoneId: string): Promise<void> => {
  await axios.post(`${API_BASE}/zones/${zoneId}/disable`)
}

export const getDevices = async (): Promise<Device[]> => {
  const response = await axios.get(`${API_BASE}/devices`)
  return response.data.devices
}

export const getStatus = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/status`)
  return response.data
}
