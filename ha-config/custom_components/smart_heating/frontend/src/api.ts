import axios from 'axios'
import { Zone, Device, ZoneCreate, DeviceAdd } from './types'

const API_BASE = '/api/smart_heating'

export const getZones = async (): Promise<Area[]> => {
  const response = await axios.get(`${API_BASE}/areas`)
  return response.data.zones
}

export const getZone = async (areaId: string): Promise<Area> => {
  const response = await axios.get(`${API_BASE}/areas/${areaId}`)
  return response.data
}

export const createZone = async (data: AreaCreate): Promise<Area> => {
  const response = await axios.post(`${API_BASE}/areas`, data)
  return response.data.zone
}

export const deleteZone = async (areaId: string): Promise<void> => {
  await axios.delete(`${API_BASE}/areas/${areaId}`)
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

export const getDevices = async (): Promise<Device[]> => {
  const response = await axios.get(`${API_BASE}/devices`)
  return response.data.devices
}

export const getStatus = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/status`)
  return response.data
}
