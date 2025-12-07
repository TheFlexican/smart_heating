import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { 
  ThemeProvider, 
  createTheme, 
  CssBaseline, 
  Box, 
  Snackbar, 
  Alert 
} from '@mui/material'
import { DragDropContext, DropResult } from 'react-beautiful-dnd'
import Header from './components/Header'
import ZoneList from './components/ZoneList'
import DevicePanel from './components/DevicePanel'
import OpenThermStatus from './components/OpenThermStatus'
import { VacationModeBanner } from './components/VacationModeBanner'
import ZoneDetail from './pages/AreaDetail'
import GlobalSettings from './pages/GlobalSettings'
import { Zone, Device } from './types'
import { getZones, getDevices, addDeviceToZone, getConfig, getSafetySensor } from './api'
import { useWebSocket } from './hooks/useWebSocket'

// Home Assistant color scheme - matches HA's native dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#03a9f4', // HA blue accent
      light: '#42c0fb',
      dark: '#0286c2',
    },
    secondary: {
      main: '#ffc107', // HA amber accent
      light: '#ffd54f',
      dark: '#c79100',
    },
    background: {
      default: '#111111', // HA dark background
      paper: '#1c1c1c',   // HA card background
    },
    text: {
      primary: '#e1e1e1',
      secondary: '#9e9e9e',
    },
    divider: '#2c2c2c',
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
})

interface ZonesOverviewProps {
  wsConnected: boolean
  safetyAlertActive: boolean
  openthermConfig: { gateway_id?: string; enabled?: boolean }
  areas: Zone[]
  loading: boolean
  showHidden: boolean
  availableDevices: Device[]
  handleDragEnd: (result: DropResult) => void
  handleZonesUpdate: () => void
  setShowHidden: (value: boolean) => void
}

const ZonesOverview = ({
  wsConnected,
  safetyAlertActive,
  openthermConfig,
  areas,
  loading,
  showHidden,
  availableDevices,
  handleDragEnd,
  handleZonesUpdate,
  setShowHidden,
}: ZonesOverviewProps) => (
  <DragDropContext onDragEnd={handleDragEnd}>
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100vh',
      bgcolor: 'background.default'
    }}>
      <Header wsConnected={wsConnected} />
      <Box sx={{ 
        display: 'flex', 
        flex: 1, 
        overflow: 'hidden',
        flexDirection: { xs: 'column', md: 'row' }
      }}>
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: { xs: 1.5, sm: 2, md: 3 },
          bgcolor: 'background.default' 
        }}>
          {safetyAlertActive && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              icon={<span style={{ fontSize: '24px' }}>🚨</span>}
            >
              <strong>SAFETY ALERT ACTIVE!</strong> All heating has been shut down due to a safety sensor alert. 
              Please resolve the safety issue and manually re-enable areas in Settings.
            </Alert>
          )}
          <VacationModeBanner />
          <OpenThermStatus 
            openthermGatewayId={openthermConfig.gateway_id}
            enabled={openthermConfig.enabled}
          />
          <ZoneList 
            areas={areas} 
            loading={loading}
            onUpdate={handleZonesUpdate}
            showHidden={showHidden}
            onToggleShowHidden={() => setShowHidden(!showHidden)}
          />
        </Box>
        <Box sx={{ display: { xs: 'none', md: 'block' } }}>
          <DevicePanel 
            devices={availableDevices}
            onUpdate={handleZonesUpdate}
          />
        </Box>
      </Box>
    </Box>
  </DragDropContext>
)

function App() {
  const [areas, setAreas] = useState<Zone[]>([])
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [showConnectionAlert, setShowConnectionAlert] = useState(false)
  const [showHidden, setShowHidden] = useState(false)
  const [openthermConfig, setOpenthermConfig] = useState<{
    gateway_id?: string
    enabled?: boolean
  }>({})
  const [safetyAlertActive, setSafetyAlertActive] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [areasData, devicesData, configData, safetySensorData] = await Promise.all([
        getZones(),
        getDevices(),
        getConfig(),
        getSafetySensor().catch(() => null)
      ])
      setAreas(areasData)
      
      // Check if safety alert is active
      if (safetySensorData?.alert_active) {
        setSafetyAlertActive(true)
      } else {
        setSafetyAlertActive(false)
      }
      
      // Store OpenTherm config
      setOpenthermConfig({
        gateway_id: configData.opentherm_gateway_id,
        enabled: configData.opentherm_enabled
      })
      
      // Filter out devices already assigned to areas
      const assignedDeviceIds = new Set(
        areasData.flatMap(area => area.devices.map(d => d.id))
      )
      setAvailableDevices(
        devicesData.filter(device => !assignedDeviceIds.has(device.id))
      )
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  // WebSocket connection for real-time updates
  useWebSocket({
    onConnect: () => {
      setWsConnected(true)
      setShowConnectionAlert(false)
      // Reload safety sensor status when reconnecting
      getSafetySensor()
        .then(data => setSafetyAlertActive(data?.alert_active || false))
        .catch(() => setSafetyAlertActive(false))
    },
    onDisconnect: () => {
      setWsConnected(false)
      setShowConnectionAlert(true)
    },
    onZonesUpdate: (updatedZones) => {
      // Backend now includes hidden property, no need to preserve from previous state
      setAreas(updatedZones)
      // Reload devices to update available list
      const assignedDeviceIds = new Set<string>()
      for (const area of updatedZones) {
        for (const d of area.devices) {
          assignedDeviceIds.add(d.id)
        }
      }
      getDevices().then(devicesData => {
        setAvailableDevices(
          devicesData.filter(device => !assignedDeviceIds.has(device.id))
        )
      })
      // Also refresh safety sensor status
      getSafetySensor()
        .then(data => setSafetyAlertActive(data?.alert_active || false))
        .catch(() => setSafetyAlertActive(false))
    },
    onZoneUpdate: (updatedZone) => {
      setAreas(prevAreas => 
        prevAreas.map(z => z.id === updatedZone.id ? updatedZone : z)
      )
    },
    onZoneDelete: (areaId) => {
      setAreas(prevAreas => prevAreas.filter(z => z.id !== areaId))
      // Reload data to update available devices
      loadData()
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
    }
  })

  useEffect(() => {
    loadData()
  }, [])

  const handleZonesUpdate = () => {
    loadData()
  }

  const handleDragEnd = async (result: DropResult) => {
    const { source, destination } = result

    if (!destination) return
    if (source.droppableId === destination.droppableId) return

    const areaId = destination.droppableId.replace('area-', '')
    const deviceId = result.draggableId.replace('device-', '')
    
    const device = availableDevices.find(d => d.id === deviceId)
    if (!device) return
    
    try {
      await addDeviceToZone(areaId, {
        device_id: deviceId,
        device_type: device.type,
        mqtt_topic: device.mqtt_topic
      })
      await loadData()
    } catch (error) {
      console.error('Failed to add device to area:', error)
    }
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router basename="/smart_heating_ui">
        <Routes>
          <Route path="/" element={
            <ZonesOverview 
              wsConnected={wsConnected}
              safetyAlertActive={safetyAlertActive}
              openthermConfig={openthermConfig}
              areas={areas}
              loading={loading}
              showHidden={showHidden}
              availableDevices={availableDevices}
              handleDragEnd={handleDragEnd}
              handleZonesUpdate={handleZonesUpdate}
              setShowHidden={setShowHidden}
            />
          } />
          <Route path="/area/:areaId" element={<ZoneDetail />} />
          <Route path="/settings/global" element={<GlobalSettings />} />
        </Routes>
      </Router>
      
      {/* Connection status notification */}
      <Snackbar
        open={showConnectionAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        autoHideDuration={null}
      >
        <Alert 
          severity="warning" 
          onClose={() => setShowConnectionAlert(false)}
          sx={{ width: '100%' }}
        >
          WebSocket disconnected. Real-time updates disabled.
        </Alert>
      </Snackbar>
    </ThemeProvider>
  )
}

export default App
