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
import Header from './components/Header'
import ZoneList from './components/ZoneList'
import DevicePanel from './components/DevicePanel'
import { VacationModeBanner } from './components/VacationModeBanner'
import ZoneDetail from './pages/AreaDetail'
import GlobalSettings from './pages/GlobalSettings'
import { UserManagement } from './components/UserManagement'
import EfficiencyReports from './components/EfficiencyReports'
import HistoricalComparisons from './components/HistoricalComparisons'
import AdvancedMetricsDashboard from './components/AdvancedMetricsDashboard'
import { Zone, Device } from './types'
import { getZones, getDevices, getConfig, getSafetySensor } from './api'
import { useWebSocket } from './hooks/useWebSocket'

// Home Assistant theme factory - matches HA's native theme
const createHATheme = (mode: 'light' | 'dark') => createTheme({
  palette: {
    mode,
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
    background: mode === 'dark' ? {
      default: '#111111', // HA dark background
      paper: '#1c1c1c',   // HA card background
    } : {
      default: '#fafafa', // HA light background
      paper: '#ffffff',   // HA light card background
    },
    text: mode === 'dark' ? {
      primary: '#e1e1e1',
      secondary: '#9e9e9e',
    } : {
      primary: '#212121',
      secondary: '#757575',
    },
    divider: mode === 'dark' ? '#2c2c2c' : '#e0e0e0',
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
  areas: Zone[]
  loading: boolean
  showHidden: boolean
  hideDevicesPanel: boolean
  availableDevices: Device[]
  handleZonesUpdate: () => void
  setShowHidden: (value: boolean) => void
  onAreasReorder: (areas: Zone[]) => void
}

const ZonesOverview = ({
  wsConnected,
  safetyAlertActive,
  areas,
  loading,
  showHidden,
  hideDevicesPanel,
  availableDevices,
  handleZonesUpdate,
  setShowHidden,
  onAreasReorder,
}: ZonesOverviewProps) => (
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
          <ZoneList
            areas={areas}
            loading={loading}
            onUpdate={handleZonesUpdate}
            showHidden={showHidden}
            onToggleShowHidden={() => setShowHidden(!showHidden)}
            onAreasReorder={onAreasReorder}
          />
        </Box>
        {!hideDevicesPanel && (
          <Box sx={{ display: { xs: 'none', md: 'block' } }}>
            <DevicePanel
              devices={availableDevices}
              onUpdate={handleZonesUpdate}
            />
          </Box>
        )}
      </Box>
    </Box>
)

function App() {
  const [areas, setAreas] = useState<Zone[]>([])
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [showConnectionAlert, setShowConnectionAlert] = useState(false)
  const [showHidden, setShowHidden] = useState(false)
  const [hideDevicesPanel, setHideDevicesPanel] = useState(false)
  const [safetyAlertActive, setSafetyAlertActive] = useState(false)
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(() => {
    // Load theme preference from localStorage
    const saved = localStorage.getItem('appThemeMode')
    return (saved === 'light' || saved === 'dark') ? saved : 'dark'
  })

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [areasData, devicesData, configData, safetySensorData] = await Promise.all([
        getZones(),
        getDevices(),
        getConfig(),
        getSafetySensor().catch(() => null)
      ])

      // Apply saved area order from localStorage
      const savedOrder = localStorage.getItem('areasOrder')
      let orderedAreas = areasData
      if (savedOrder) {
        try {
          const orderIds = JSON.parse(savedOrder)
          const areaMap = new Map(areasData.map(a => [a.id, a]))
          orderedAreas = orderIds
            .map((id: string) => areaMap.get(id))
            .filter((a: Zone | undefined): a is Zone => a !== undefined)
          // Add any new areas that weren't in the saved order
          const orderedIds = new Set(orderIds)
          const newAreas = areasData.filter(a => !orderedIds.has(a.id))
          orderedAreas = [...orderedAreas, ...newAreas]
        } catch {
          // If parsing fails, use default order
        }
      }

      setAreas(orderedAreas)

      // Check if safety alert is active
      if (safetySensorData?.alert_active) {
        setSafetyAlertActive(true)
      } else {
        setSafetyAlertActive(false)
      }

      // Store hide devices panel setting
      setHideDevicesPanel(configData.hide_devices_panel || false)

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
      // Preserve any client-side area ordering preference stored in localStorage
      // when receiving full zones update from the backend. This prevents
      // periodic WS updates from reverting user-configured order.
      const savedOrder = localStorage.getItem('areasOrder')
      let orderedZones = updatedZones
      if (savedOrder) {
        try {
          const orderIds = JSON.parse(savedOrder)
          const zoneMap = new Map(updatedZones.map(a => [a.id, a]))
          orderedZones = orderIds
            .map((id: string) => zoneMap.get(id))
            .filter((a: Zone | undefined): a is Zone => a !== undefined)
          // Append any new zones not present in saved order
          const orderedIds = new Set(orderIds)
          const newZones = updatedZones.filter(a => !orderedIds.has(a.id))
          orderedZones = [...orderedZones, ...newZones]
        } catch {
          // parsing failed, fall back to backend order
          orderedZones = updatedZones
        }
      }

      // Backend now includes hidden property, no need to preserve from previous state
      setAreas(orderedZones)
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

  // Save theme preference to localStorage when changed
  useEffect(() => {
    localStorage.setItem('appThemeMode', themeMode)
  }, [themeMode])

  useEffect(() => {
    loadData()
  }, [])

  const handleZonesUpdate = () => {
    loadData()
  }

  // Device drag-drop temporarily disabled - will be re-implemented with @dnd-kit

  return (
    <ThemeProvider theme={createHATheme(themeMode)}>
      <CssBaseline />
      <Router basename="/smart_heating_ui">
        <Routes>
          <Route path="/" element={
            <ZonesOverview
              wsConnected={wsConnected}
              safetyAlertActive={safetyAlertActive}
              areas={areas}
              loading={loading}
              showHidden={showHidden}
              hideDevicesPanel={hideDevicesPanel}
              availableDevices={availableDevices}
              handleZonesUpdate={handleZonesUpdate}
              setShowHidden={setShowHidden}
              onAreasReorder={(reorderedAreas) => {
                setAreas(reorderedAreas)
                // Persist to localStorage
                const orderIds = reorderedAreas.map(a => a.id)
                localStorage.setItem('areasOrder', JSON.stringify(orderIds))
              }}
            />
          } />
          <Route path="/area/:areaId" element={<ZoneDetail />} />
          <Route path="/settings/global" element={<GlobalSettings themeMode={themeMode} onThemeChange={setThemeMode} />} />
          <Route path="/settings/users" element={<UserManagement />} />
          <Route path="/analytics/efficiency" element={<EfficiencyReports />} />
          <Route path="/analytics/comparison" element={<HistoricalComparisons />} />
          <Route path="/opentherm/metrics" element={<AdvancedMetricsDashboard />} />
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
