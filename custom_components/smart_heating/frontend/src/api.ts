import axios from 'axios'
import { Area, Device, DeviceAdd, ScheduleEntry, LearningStats } from './types'

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

export const getDevices = async (): Promise<Device[]> => {
  const response = await axios.get(`${API_BASE}/devices`)
  return response.data.devices
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
