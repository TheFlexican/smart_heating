import { useState, useEffect } from 'react'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import { Box } from '@mui/material'
import Header from './components/Header'
import ZoneList from './components/ZoneList'
import DevicePanel from './components/DevicePanel'
import { Zone, Device } from './types'
import { getZones, getDevices } from './api'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#03a9f4',
    },
    secondary: {
      main: '#ff9800',
    },
  },
})

function App() {
  const [zones, setZones] = useState<Area[]>([])
  const [devices, setDevices] = useState<Device[]>([])
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [zonesData, devicesData] = await Promise.all([
        getZones(),
        getDevices()
      ])
      setZones(zonesData)
      setDevices(devicesData)
      
      // Filter out devices already assigned to zones
      const assignedDeviceIds = new Set(
        zonesData.flatMap(zone => zone.devices.map(d => d.id))
      )
      setAvailableDevices(
        devicesData.filter(device => !assignedDeviceIds.has(device.id))
      )
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleZonesUpdate = () => {
    loadData()
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <Header />
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
            <ZoneList 
              zones={zones} 
              loading={loading}
              onUpdate={handleZonesUpdate}
            />
          </Box>
          <DevicePanel 
            devices={availableDevices}
            onUpdate={handleZonesUpdate}
          />
        </Box>
      </Box>
    </ThemeProvider>
  )
}

export default App
