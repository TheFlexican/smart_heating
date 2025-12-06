import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tabs,
  Tab,
  CircularProgress,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Slider,
  Switch,
  Divider,
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import TuneIcon from '@mui/icons-material/Tune'
import NightsStayIcon from '@mui/icons-material/NightsStay'
import PsychologyIcon from '@mui/icons-material/Psychology'
import WindowIcon from '@mui/icons-material/Window'
import SensorOccupiedIcon from '@mui/icons-material/SensorOccupied'
import HistoryIcon from '@mui/icons-material/History'
import SpeedIcon from '@mui/icons-material/Speed'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import { Zone, WindowSensorConfig, PresenceSensorConfig, Device } from '../types'
import { 
  getZones, 
  setZoneTemperature, 
  enableZone, 
  disableZone, 
  setPresetMode,
  setBoostMode,
  cancelBoost,
  setHvacMode,
  addWindowSensor,
  removeWindowSensor,
  addPresenceSensor,
  removePresenceSensor,
  getHistoryConfig,
  setHistoryRetention,
  getDevices,
  addDeviceToZone,
  removeDeviceFromZone
} from '../api'
import ScheduleEditor from '../components/ScheduleEditor'
import HistoryChart from '../components/HistoryChart'
import SensorConfigDialog from '../components/SensorConfigDialog'
import DraggableSettings, { SettingSection } from '../components/DraggableSettings'
import { useWebSocket } from '../hooks/useWebSocket'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`area-tabpanel-${index}`}
      aria-labelledby={`area-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const ZoneDetail = () => {
  const { areaId } = useParams<{ areaId: string }>()
  const navigate = useNavigate()
  const [area, setZone] = useState<Zone | null>(null)
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [showOnlyHeating, setShowOnlyHeating] = useState(true)
  const [deviceSearch, setDeviceSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [tabValue, setTabValue] = useState(0)
  const [temperature, setTemperature] = useState(21)
  const [historyRetention, setHistoryRetentionState] = useState(30)
  const [recordInterval, setRecordInterval] = useState(5)
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [sensorDialogType, setSensorDialogType] = useState<'window' | 'presence'>('window')
  const [expandedCard, setExpandedCard] = useState<string | null>(null) // Accordion state

  // WebSocket for real-time updates
  useWebSocket({
    onZoneUpdate: (updatedZone) => {
      if (updatedZone.id === areaId) {
        setZone(updatedZone)
        setTemperature(updatedZone.target_temperature)
      }
    },
    onZonesUpdate: (areas) => {
      const currentZone = areas.find(z => z.id === areaId)
      if (currentZone) {
        setZone(currentZone)
        setTemperature(currentZone.target_temperature)
      }
    },
  })

  useEffect(() => {
    loadData()
    loadHistoryConfig()
  }, [areaId])

  const loadData = async () => {
    if (!areaId) return
    
    try {
      setLoading(true)
      const areasData = await getZones()
      
      const currentZone = areasData.find(z => z.id === areaId)
      if (!currentZone) {
        navigate('/')
        return
      }
      
      setZone(currentZone)
      setTemperature(currentZone.target_temperature)
      
      // Load available devices
      await loadAvailableDevices(currentZone)
    } catch (error) {
      console.error('Failed to load area:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadAvailableDevices = async (currentZone: Zone) => {
    try {
      const allDevices = await getDevices()
      
      // Filter devices:
      // 1. Must be assigned to the same HA area as this zone (by area_id OR name matching)
      // 2. Must NOT already be assigned to this zone
      const available = allDevices.filter(device => {
        // Check if already assigned
        const alreadyAssigned = currentZone.devices.some(d => 
          (d.entity_id || d.id) === (device.entity_id || device.id)
        )
        if (alreadyAssigned) return false
        
        // Method 1: Direct HA area match
        if (device.ha_area_id === currentZone.id) {
          return true
        }
        
        // Method 2: Name-based matching (for MQTT devices without HA area assignment)
        // Check if device name contains the zone name
        const zoneName = currentZone.name.toLowerCase()
        const deviceName = (device.name || device.entity_id || device.id || '').toLowerCase()
        if (deviceName.includes(zoneName)) {
          return true
        }
        
        return false
      })
      
      setAvailableDevices(available)
    } catch (error) {
      console.error('Failed to load available devices:', error)
    }
  }
  
  const loadHistoryConfig = async () => {
    try {
      const config = await getHistoryConfig()
      setHistoryRetentionState(config.retention_days)
      setRecordInterval(config.record_interval_minutes)
    } catch (error) {
      console.error('Failed to load history config:', error)
    }
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleToggle = async () => {
    if (!area) return
    
    try {
      if (area.enabled) {
        await disableZone(area.id)
      } else {
        await enableZone(area.id)
      }
      await loadData()
    } catch (error) {
      console.error('Failed to toggle area:', error)
    }
  }

  const handleTemperatureChange = (_event: Event, value: number | number[]) => {
    setTemperature(value as number)
  }

  const handleTemperatureCommit = async (_event: Event | React.SyntheticEvent, value: number | number[]) => {
    if (!area) return
    
    try {
      await setZoneTemperature(area.id, value as number)
      await loadData()
    } catch (error) {
      console.error('Failed to set temperature:', error)
    }
  }

  const getDeviceStatusIcon = (device: any) => {
    if (device.type === 'thermostat') {
      // Check if should be heating based on area target temperature (not device's stale target)
      const shouldHeat = area && area.target_temperature !== undefined && 
                        device.current_temperature !== undefined && 
                        area.target_temperature > device.current_temperature
      
      if (shouldHeat) {
        return <LocalFireDepartmentIcon fontSize="small" sx={{ color: 'error.main' }} />
      } else if (device.state === 'heat') {
        return <ThermostatIcon fontSize="small" sx={{ color: 'primary.main' }} />
      } else {
        return <AcUnitIcon fontSize="small" sx={{ color: 'info.main' }} />
      }
    } else if (device.type === 'valve') {
      return <TuneIcon fontSize="small" sx={{ color: device.position > 0 ? 'warning.main' : 'text.secondary' }} />
    } else if (device.type === 'temperature_sensor') {
      return <SensorsIcon fontSize="small" sx={{ color: 'success.main' }} />
    } else {
      return <PowerSettingsNewIcon fontSize="small" sx={{ color: device.state === 'on' ? 'success.main' : 'text.secondary' }} />
    }
  }

  const getDeviceStatus = (device: any) => {
    if (device.type === 'thermostat') {
      const parts = []
      if (device.current_temperature !== undefined && device.current_temperature !== null) {
        parts.push(`${device.current_temperature.toFixed(1)}°C`)
      }
      // Use area target temperature instead of device's stale target
      if (area && area.target_temperature !== undefined && area.target_temperature !== null && 
          device.current_temperature !== undefined && device.current_temperature !== null &&
          area.target_temperature > device.current_temperature) {
        parts.push(`→ ${area.target_temperature.toFixed(1)}°C`)
      }
      return parts.length > 0 ? parts.join(' · ') : device.state || 'unknown'
    } else if (device.type === 'temperature_sensor') {
      if (device.temperature !== undefined && device.temperature !== null) {
        return `${device.temperature.toFixed(1)}°C`
      }
      return device.state || 'unknown'
    } else if (device.type === 'valve') {
      const parts = []
      if (device.position !== undefined) {
        parts.push(`${device.position}%`)
      }
      if (device.state) {
        parts.push(device.state)
      }
      return parts.length > 0 ? parts.join(' · ') : 'unknown'
    } else {
      return device.state || 'unknown'
    }
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'heating':
        return 'error'
      case 'idle':
        return 'info'
      case 'off':
        return 'default'
      default:
        return 'default'
    }
  }

  // Generate settings sections for draggable layout
  const getSettingsSections = (): SettingSection[] => {
    if (!area) return []

    return [
      {
        id: 'preset-modes',
        title: 'Preset Modes',
        description: 'Quick temperature presets for different scenarios',
        icon: <BookmarkIcon />,
        badge: area.preset_mode !== 'none' ? area.preset_mode : undefined,
        defaultExpanded: false,
        content: (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Current Preset</InputLabel>
              <Select
                value={area.preset_mode || 'none'}
                label="Current Preset"
                onChange={async (e) => {
                  try {
                    await setPresetMode(area.id, e.target.value)
                    loadData()
                  } catch (error) {
                    console.error('Failed to set preset mode:', error)
                  }
                }}
              >
                <MenuItem value="none">None (Manual)</MenuItem>
                <MenuItem value="away">Away ({area.away_temp ?? 16}°C)</MenuItem>
                <MenuItem value="eco">Eco ({area.eco_temp ?? 18}°C)</MenuItem>
                <MenuItem value="comfort">Comfort ({area.comfort_temp ?? 22}°C)</MenuItem>
                <MenuItem value="home">Home ({area.home_temp ?? 21}°C)</MenuItem>
                <MenuItem value="sleep">Sleep ({area.sleep_temp ?? 19}°C)</MenuItem>
                <MenuItem value="activity">Activity ({area.activity_temp ?? 23}°C)</MenuItem>
                <MenuItem value="boost">Boost (See Boost Mode)</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info">
              Preset temperatures can be configured via Home Assistant services. Current preset: <strong>{area.preset_mode || 'none'}</strong>
            </Alert>
          </>
        )
      },
      {
        id: 'boost-mode',
        title: 'Boost Mode',
        description: 'Temporarily increase temperature for a specified duration',
        icon: <SpeedIcon />,
        badge: area.boost_mode_active ? 'ACTIVE' : undefined,
        defaultExpanded: area.boost_mode_active,
        content: area.boost_mode_active ? (
          <Box>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Boost mode is <strong>ACTIVE</strong>! Temperature: {area.boost_temp}°C, Duration: {area.boost_duration} minutes
            </Alert>
            <Button 
              variant="outlined" 
              color="error"
              onClick={async () => {
                try {
                  await cancelBoost(area.id)
                  loadData()
                } catch (error) {
                  console.error('Failed to cancel boost:', error)
                }
              }}
            >
              Cancel Boost Mode
            </Button>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
            <TextField
              label="Boost Temperature"
              type="number"
              defaultValue={25}
              inputProps={{ min: 15, max: 30, step: 0.5 }}
              sx={{ flex: 1 }}
              id="boost-temp-input"
            />
            <TextField
              label="Duration (minutes)"
              type="number"
              defaultValue={60}
              inputProps={{ min: 5, max: 180, step: 5 }}
              sx={{ flex: 1 }}
              id="boost-duration-input"
            />
            <Button 
              variant="contained" 
              color="primary"
              onClick={async () => {
                try {
                  const tempInput = document.getElementById('boost-temp-input') as HTMLInputElement
                  const durationInput = document.getElementById('boost-duration-input') as HTMLInputElement
                  const temp = parseFloat(tempInput.value)
                  const duration = parseInt(durationInput.value)
                  await setBoostMode(area.id, duration, temp)
                  loadData()
                } catch (error) {
                  console.error('Failed to activate boost:', error)
                }
              }}
            >
              Activate Boost
            </Button>
          </Box>
        )
      },
      {
        id: 'hvac-mode',
        title: 'HVAC Mode',
        description: 'Control the heating/cooling mode for this area',
        icon: <TuneIcon />,
        badge: area.hvac_mode || 'heat',
        defaultExpanded: false,
        content: (
          <FormControl fullWidth>
            <InputLabel>HVAC Mode</InputLabel>
            <Select
              value={area.hvac_mode || 'heat'}
              label="HVAC Mode"
              onChange={async (e) => {
                try {
                  await setHvacMode(area.id, e.target.value)
                  loadData()
                } catch (error) {
                  console.error('Failed to set HVAC mode:', error)
                }
              }}
            >
              <MenuItem value="heat">Heat</MenuItem>
              <MenuItem value="cool">Cool</MenuItem>
              <MenuItem value="auto">Auto</MenuItem>
              <MenuItem value="off">Off</MenuItem>
            </Select>
          </FormControl>
        )
      },
      {
        id: 'window-sensors',
        title: 'Window Sensors',
        description: 'Automatically adjust heating when windows are open',
        icon: <WindowIcon />,
        badge: area.window_sensors?.length || undefined,
        defaultExpanded: false,
        content: (
          <>
            {area.window_sensors && area.window_sensors.length > 0 ? (
              <List dense>
                {area.window_sensors.map((sensor) => {
                  const sensorConfig = typeof sensor === 'string' 
                    ? { entity_id: sensor, action_when_open: 'reduce_temperature', temp_drop: 5 }
                    : sensor
                  
                  let secondaryText = ''
                  if (sensorConfig.action_when_open === 'turn_off') {
                    secondaryText = 'Turn off heating when open'
                  } else if (sensorConfig.action_when_open === 'reduce_temperature') {
                    secondaryText = `Reduce temperature by ${sensorConfig.temp_drop}°C when open`
                  } else {
                    secondaryText = 'No action when open'
                  }
                  
                  return (
                    <ListItem
                      key={sensorConfig.entity_id}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={async () => {
                            try {
                              await removeWindowSensor(area.id, sensorConfig.entity_id)
                              loadData()
                            } catch (error) {
                              console.error('Failed to remove window sensor:', error)
                            }
                          }}
                        >
                          <RemoveCircleOutlineIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText 
                        primary={sensorConfig.entity_id}
                        secondary={secondaryText}
                      />
                    </ListItem>
                  )
                })}
              </List>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                No window sensors configured. Add binary sensors to enable window detection.
              </Alert>
            )}
            
            <Button
              variant="outlined"
              fullWidth
              onClick={() => {
                setSensorDialogType('window')
                setSensorDialogOpen(true)
              }}
            >
              Add Window Sensor
            </Button>
          </>
        )
      },
      {
        id: 'presence-sensors',
        title: 'Presence Sensors',
        description: 'Adjust heating based on presence/motion detection',
        icon: <SensorOccupiedIcon />,
        badge: area.presence_sensors?.length || undefined,
        defaultExpanded: false,
        content: (
          <>
            {area.presence_sensors && area.presence_sensors.length > 0 ? (
              <List dense>
                {area.presence_sensors.map((sensor) => {
                  const sensorConfig = typeof sensor === 'string'
                    ? { entity_id: sensor, action_when_away: 'reduce_temperature', action_when_home: 'increase_temperature', temp_drop_when_away: 3, temp_boost_when_home: 2 }
                    : sensor
                  
                  let awayText = ''
                  if (sensorConfig.action_when_away === 'turn_off') {
                    awayText = 'Turn off heating'
                  } else if (sensorConfig.action_when_away === 'reduce_temperature') {
                    awayText = `Reduce by ${sensorConfig.temp_drop_when_away}°C`
                  } else if (sensorConfig.action_when_away === 'set_eco') {
                    awayText = 'Set to Eco mode'
                  } else {
                    awayText = 'No action'
                  }
                  
                  let homeText = ''
                  if (sensorConfig.action_when_home === 'set_comfort') {
                    homeText = 'Set to Comfort mode'
                  } else if (sensorConfig.action_when_home === 'increase_temperature') {
                    homeText = `Increase by +${sensorConfig.temp_boost_when_home}°C`
                  } else {
                    homeText = 'No action'
                  }
                  
                  return (
                    <ListItem
                      key={sensorConfig.entity_id}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={async () => {
                            try {
                              await removePresenceSensor(area.id, sensorConfig.entity_id)
                              loadData()
                            } catch (error) {
                              console.error('Failed to remove presence sensor:', error)
                            }
                          }}
                        >
                          <RemoveCircleOutlineIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText 
                        primary={sensorConfig.entity_id}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.secondary" display="block">
                              When away: {awayText}
                            </Typography>
                            <Typography component="span" variant="body2" color="text.secondary" display="block">
                              When home: {homeText}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  )
                })}
              </List>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                No presence sensors configured. Add binary sensors to enable presence detection.
              </Alert>
            )}
            
            <Button
              variant="outlined"
              fullWidth
              onClick={() => {
                setSensorDialogType('presence')
                setSensorDialogOpen(true)
              }}
            >
              Add Presence Sensor
            </Button>
          </>
        )
      },
      {
        id: 'night-boost',
        title: 'Night Boost Settings',
        description: 'Gradually increase temperature during night hours for morning comfort',
        icon: <NightsStayIcon />,
        badge: area.night_boost_enabled ? 'ON' : 'OFF',
        defaultExpanded: false,
        content: (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="body1" color="text.primary">
                  Enable Night Boost
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Automatically add temperature offset during night hours
                </Typography>
              </Box>
              <Switch
                checked={area.night_boost_enabled ?? true}
                onChange={async (e) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_enabled: e.target.checked
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update night boost:', error)
                  }
                }}
              />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Night Boost Period
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                label="Start Time"
                type="time"
                value={area.night_boost_start_time ?? '22:00'}
                onChange={async (e) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_start_time: e.target.value
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update night boost start time:', error)
                  }
                }}
                disabled={!area.night_boost_enabled}
                InputLabelProps={{ shrink: true }}
                inputProps={{ step: 300 }}
                sx={{ flex: 1 }}
              />
              <TextField
                label="End Time"
                type="time"
                value={area.night_boost_end_time ?? '06:00'}
                onChange={async (e) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_end_time: e.target.value
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update night boost end time:', error)
                  }
                }}
                disabled={!area.night_boost_enabled}
                InputLabelProps={{ shrink: true }}
                inputProps={{ step: 300 }}
                sx={{ flex: 1 }}
              />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Night Boost Temperature Offset
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Slider
                value={area.night_boost_offset ?? 0.5}
                onChange={async (_e, value) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        night_boost_offset: value
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update night boost offset:', error)
                  }
                }}
                min={0}
                max={3}
                step={0.1}
                marks={[
                  { value: 0, label: '0°C' },
                  { value: 1.5, label: '1.5°C' },
                  { value: 3, label: '3°C' }
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `+${value}°C`}
                disabled={!area.night_boost_enabled}
                sx={{ flexGrow: 1 }}
              />
              <Typography variant="h6" color="primary" sx={{ minWidth: 60 }}>
                +{area.night_boost_offset ?? 0.5}°C
              </Typography>
            </Box>
          </>
        )
      },
      {
        id: 'smart-night-boost',
        title: 'Smart Night Boost (AI Learning)',
        description: 'ML-based optimal heating start time prediction',
        icon: <PsychologyIcon />,
        badge: area.smart_night_boost_enabled ? 'LEARNING' : 'OFF',
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" paragraph>
              Uses machine learning to predict optimal heating start time based on weather and historical data.
              The system learns how long your room takes to heat up and automatically starts heating at the right time.
            </Typography>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="body1" color="text.primary">
                  Enable Smart Night Boost
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Automatically predict and optimize heating start time
                </Typography>
              </Box>
              <Switch
                checked={area.smart_night_boost_enabled ?? false}
                onChange={async (e) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_night_boost',
                        area_id: area.id,
                        smart_night_boost_enabled: e.target.checked
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update smart night boost:', error)
                  }
                }}
              />
            </Box>

            <TextField
              label="Target Wake-up Time"
              type="time"
              value={area.smart_night_boost_target_time ?? '06:00'}
              onChange={async (e) => {
                try {
                  await fetch('/api/smart_heating/call_service', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      service: 'set_night_boost',
                      area_id: area.id,
                      smart_night_boost_target_time: e.target.value
                    })
                  })
                  loadData()
                } catch (error) {
                  console.error('Failed to update target time:', error)
                }
              }}
              disabled={!area.smart_night_boost_enabled}
              fullWidth
              helperText="Time when the room should reach target temperature"
              InputLabelProps={{ shrink: true }}
              inputProps={{ step: 300 }}
              sx={{ mb: 3 }}
            />

            <TextField
              label="Outdoor Temperature Sensor"
              value={area.weather_entity_id ?? ''}
              onChange={async (e) => {
                try {
                  await fetch('/api/smart_heating/call_service', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      service: 'set_night_boost',
                      area_id: area.id,
                      weather_entity_id: e.target.value
                    })
                  })
                  loadData()
                } catch (error) {
                  console.error('Failed to update weather entity:', error)
                }
              }}
              disabled={!area.smart_night_boost_enabled}
              fullWidth
              placeholder="sensor.outdoor_temperature"
              helperText="Entity ID of outdoor temperature sensor for weather correlation"
            />

            {area.smart_night_boost_enabled && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>How it works:</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary" component="div">
                  • System tracks every heating cycle automatically<br/>
                  • Learns how weather affects heating time<br/>
                  • Predicts when to start heating to reach target by wake-up time<br/>
                  • Improves accuracy over time with more data
                </Typography>
              </Box>
            )}
          </>
        )
      },
      {
        id: 'heating-control',
        title: 'Heating Control Settings',
        description: 'Configure temperature hysteresis and limits',
        icon: <TuneIcon />,
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Temperature Hysteresis
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              Hysteresis prevents rapid on/off cycling. Heating turns on when temperature is below (target - hysteresis) and off when it reaches target.
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Global hysteresis setting affects all areas. Current value: 0.5°C
            </Alert>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
              <Slider
                defaultValue={0.5}
                onChange={async (_e, value) => {
                  try {
                    await fetch('/api/smart_heating/call_service', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        service: 'set_hysteresis',
                        hysteresis: value
                      })
                    })
                  } catch (error) {
                    console.error('Failed to update hysteresis:', error)
                  }
                }}
                min={0.1}
                max={2.0}
                step={0.1}
                marks={[
                  { value: 0.1, label: '0.1°C' },
                  { value: 1.0, label: '1.0°C' },
                  { value: 2.0, label: '2.0°C' }
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${value}°C`}
                sx={{ flexGrow: 1 }}
              />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Temperature Limits
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              Minimum and maximum temperature limits for this area
            </Typography>
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Minimum Temperature
                </Typography>
                <Typography variant="h4" color="text.primary">
                  5°C
                </Typography>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Maximum Temperature
                </Typography>
                <Typography variant="h4" color="text.primary">
                  30°C
                </Typography>
              </Box>
            </Box>
          </>
        )
      },
      {
        id: 'history-management',
        title: 'History Data Management',
        description: 'Configure temperature history retention and recording',
        icon: <HistoryIcon />,
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configure how long temperature history is stored. Data is recorded every {recordInterval} minutes and automatically cleaned up after the retention period.
            </Typography>
            
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Data Retention Period: {historyRetention} days
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2, mb: 3 }}>
              <Slider
                value={historyRetention}
                onChange={(_, value) => setHistoryRetentionState(value as number)}
                min={1}
                max={30}
                step={1}
                marks={[
                  { value: 1, label: '1d' },
                  { value: 30, label: '30d' }
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${value}d`}
                sx={{ flexGrow: 1 }}
              />
              <Button
                variant="contained"
                size="small"
                onClick={async () => {
                  try {
                    await setHistoryRetention(historyRetention)
                    await loadHistoryConfig()
                  } catch (error) {
                    console.error('Failed to update history retention:', error)
                  }
                }}
              >
                Save
              </Button>
            </Box>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <strong>Note:</strong> History data older than the retention period will be automatically deleted during the next cleanup cycle (runs every hour). 
              Reducing the retention period will trigger an immediate cleanup. Recording interval is fixed at {recordInterval} minutes and cannot be changed.
            </Alert>
          </>
        )
      },
    ]
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!area) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Zone not found</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mt: 2 }}>
          Back to Zones
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => navigate('/')} edge="start">
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h5" color="text.primary">
                {area.name}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip
                  label={area.state.toUpperCase()}
                  color={getStateColor(area.state)}
                  size="small"
                />
                <Chip
                  label={area.enabled ? 'ENABLED' : 'DISABLED'}
                  color={area.enabled ? 'success' : 'default'}
                  size="small"
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mr: 2 }}>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body2" color="text.primary">
                {area.enabled ? 'Heating Active' : 'Heating Disabled'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {area.enabled ? 'Area is being controlled' : 'No temperature control'}
              </Typography>
            </Box>
            <Switch checked={area.enabled} onChange={handleToggle} color="primary" />
          </Box>
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper
        elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Devices" />
          <Tab label="Schedule" />
          <Tab label="History" />
          <Tab label="Settings" />
          <Tab label="Learning" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Temperature Control
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Target Temperature
                </Typography>
                <Typography variant="h4" color="primary">
                  {temperature}°C
                </Typography>
              </Box>
              <Slider
                value={temperature}
                onChange={handleTemperatureChange}
                onChangeCommitted={handleTemperatureCommit}
                min={5}
                max={30}
                step={0.5}
                marks={[
                  { value: 5, label: '5°' },
                  { value: 15, label: '15°' },
                  { value: 20, label: '20°' },
                  { value: 25, label: '25°' },
                  { value: 30, label: '30°' }
                ]}
                valueLabelDisplay="auto"
                disabled={!area.enabled}
              />

              {area.current_temperature !== undefined && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body1" color="text.secondary">
                      Current Temperature
                    </Typography>
                    <Typography variant="h5" color="text.primary">
                      {area.current_temperature?.toFixed(1)}°C
                    </Typography>
                  </Box>
                </>
              )}
            </Paper>

            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Device Status
              </Typography>
              {area.devices.length === 0 ? (
                <Alert severity="info">
                  No devices assigned to this area.
                </Alert>
              ) : (
                <List>
                  {area.devices.map((device) => (
                    <ListItem
                      key={device.id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemIcon>
                        {getDeviceStatusIcon(device)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body1" color="text.primary">
                              {device.name || device.id}
                            </Typography>
                            {device.type === 'thermostat' && area && 
                             area.target_temperature !== undefined && 
                             device.current_temperature !== undefined && 
                             area.target_temperature > device.current_temperature && (
                              <Chip 
                                label="heating" 
                                size="small" 
                                color="error"
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {device.type.replace(/_/g, ' ')}
                            </Typography>
                            <Typography variant="body2" color="text.primary" sx={{ mt: 0.5 }}>
                              {getDeviceStatus(device)}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Quick Stats
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="Devices"
                    secondary={`${area.devices.length} device(s) assigned`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={area.state}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Zone ID"
                    secondary={area.id}
                  />
                </ListItem>
              </List>
            </Paper>
          </Box>
        </TabPanel>

        {/* Devices Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            {/* Assigned Devices */}
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Assigned Devices ({area.devices.length})
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Devices currently assigned to this area in Smart Heating
              </Typography>

              {area.devices.length === 0 ? (
                <Alert severity="info">
                  No devices assigned yet. See available devices below or use drag & drop on the main page.
                </Alert>
              ) : (
                <List>
                  {area.devices.map((device) => (
                    <ListItem
                      key={device.id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                      secondaryAction={
                        <IconButton 
                          edge="end" 
                          aria-label="remove"
                          onClick={async () => {
                            try {
                              await removeDeviceFromZone(area.id, device.entity_id || device.id)
                              await loadData()
                            } catch (error) {
                              console.error('Failed to remove device:', error)
                            }
                          }}
                        >
                          <RemoveCircleOutlineIcon />
                        </IconButton>
                      }
                    >
                      <ListItemIcon>
                        {getDeviceStatusIcon(device)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body1" color="text.primary">
                              {device.name || device.id}
                            </Typography>
                            {device.type === 'thermostat' && area && 
                             area.target_temperature !== undefined && 
                             device.current_temperature !== undefined && 
                             area.target_temperature > device.current_temperature && (
                              <Chip 
                                label="heating" 
                                size="small" 
                                color="error"
                                sx={{ height: 20, fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {device.type.replace(/_/g, ' ')}
                            </Typography>
                            <Typography variant="body2" color="text.primary" sx={{ mt: 0.5 }}>
                              {getDeviceStatus(device)}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>

            {/* Available Devices */}
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" color="text.primary">
                  Available Devices ({availableDevices.filter(device => {
                    const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                    if (!deviceSearch) return typeMatch
                    const searchLower = deviceSearch.toLowerCase()
                    const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                    const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
                    const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                    return typeMatch && (nameMatch || entityMatch || areaMatch)
                  }).length})
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showOnlyHeating}
                      onChange={(e) => setShowOnlyHeating(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Show only climate & temperature sensors"
                />
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Devices assigned to "{area.name}" in Home Assistant but not yet added to Smart Heating
              </Typography>

              {/* Search Bar */}
              <TextField
                fullWidth
                size="small"
                placeholder="Search by device name, entity ID, or area..."
                value={deviceSearch}
                onChange={(e) => setDeviceSearch(e.target.value)}
                sx={{ mb: 2 }}
              />

              {availableDevices.filter(device => {
                const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                if (!deviceSearch) return typeMatch
                const searchLower = deviceSearch.toLowerCase()
                const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
                const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                return typeMatch && (nameMatch || entityMatch || areaMatch)
              }).length === 0 ? (
                <Alert severity="info">
                  {deviceSearch
                    ? `No devices found matching "${deviceSearch}"`
                    : showOnlyHeating 
                      ? 'No climate/temperature devices available. Toggle off the filter to see all devices.'
                      : 'No additional devices available. All devices from this area are already assigned.'}
                </Alert>
              ) : (
                <List>
                  {availableDevices
                    .filter(device => {
                      const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                      if (!deviceSearch) return typeMatch
                      const searchLower = deviceSearch.toLowerCase()
                      const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                      const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
                      const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                      return typeMatch && (nameMatch || entityMatch || areaMatch)
                    })
                    .map((device) => (
                    <ListItem
                      key={device.entity_id || device.id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                      secondaryAction={
                        <Button 
                          variant="contained" 
                          size="small"
                          onClick={async () => {
                            try {
                              await addDeviceToZone(area.id, {
                                device_id: device.entity_id || device.id,
                                device_type: device.type,
                                mqtt_topic: device.mqtt_topic
                              })
                              await loadData()
                            } catch (error) {
                              console.error('Failed to add device:', error)
                            }
                          }}
                        >
                          Add
                        </Button>
                      }
                    >
                      <ListItemIcon>
                        <ThermostatIcon color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body1" color="text.primary">
                            {device.name || device.entity_id || device.id}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
                            <Chip label={device.type.replace(/_/g, ' ')} size="small" />
                            {device.subtype && (
                              <Chip label={device.subtype} size="small" color="primary" variant="outlined" />
                            )}
                            <Typography variant="caption" color="text.secondary">
                              {device.entity_id || device.id}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Box>
        </TabPanel>

        {/* Schedule Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
            <ScheduleEditor area={area} onUpdate={loadData} />
          </Box>
        </TabPanel>

        {/* History Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Temperature History (Last 24 Hours)
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Track temperature trends over time to optimize your heating schedule.
              </Typography>
              
              {area.id && (
                <HistoryChart areaId={area.id} />
              )}
            </Paper>
          </Box>
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ maxWidth: 1600, mx: 'auto', px: 2 }}>
            <DraggableSettings 
              key={`settings-${area.id}-${area.presence_sensors?.length || 0}-${area.window_sensors?.length || 0}`}
              sections={getSettingsSections()} 
              storageKey={`area-settings-order-${area.id}`}
              expandedCard={expandedCard}
              onExpandedChange={setExpandedCard}
            />
          </Box>
        </TabPanel>

        {/* Sensor Configuration Dialog */}
        <SensorConfigDialog
          open={sensorDialogOpen}
          onClose={() => setSensorDialogOpen(false)}
          onAdd={async (config) => {
            if (!area) return
            try {
              if (sensorDialogType === 'window') {
                await addWindowSensor(area.id, config as WindowSensorConfig)
              } else {
                await addPresenceSensor(area.id, config as PresenceSensorConfig)
              }
              setSensorDialogOpen(false)
              await loadData()
            } catch (error) {
              console.error('Failed to add sensor:', error)
              alert(`Failed to add sensor: ${error}`)
            }
          }}
          sensorType={sensorDialogType}
        />

        {/* Learning Tab */}
        <TabPanel value={tabValue} index={5}>
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                Adaptive Learning Statistics
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Monitor the machine learning system's performance and predictions for this area.
              </Typography>

              {area.smart_night_boost_enabled ? (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="success.main" gutterBottom>
                    ✓ Smart night boost is active
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 3 }}>
                    The system is learning from each heating cycle and will improve predictions over time.
                  </Typography>

                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, mb: 3 }}>
                    <Typography variant="body2" color="info.dark">
                      <strong>Note:</strong> Learning statistics will be available after the system has tracked several heating cycles.
                      The more data collected, the more accurate predictions become.
                    </Typography>
                  </Box>

                  <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
                    Configuration
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Target Wake-up Time:</Typography>
                      <Typography variant="body2" color="text.primary"><strong>{area.smart_night_boost_target_time ?? '06:00'}</strong></Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Weather Sensor:</Typography>
                      <Typography variant="body2" color="text.primary">
                        {area.weather_entity_id ? <strong>{area.weather_entity_id}</strong> : <em>Not configured</em>}
                      </Typography>
                    </Box>
                  </Box>

                  <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
                    Learning Process
                  </Typography>
                  <Box component="ol" sx={{ pl: 2, mt: 1 }}>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      System records each heating cycle (start/end time, temperatures)
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Calculates heating rate (°C per minute) and outdoor correlation
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Stores statistics in Home Assistant database
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Uses historical data to predict future heating times
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary">
                      Automatically starts heating to reach target by wake-up time
                    </Typography>
                  </Box>

                  <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>API Endpoint:</strong> /api/smart_heating/areas/{area.id}/learning
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ mt: 3, textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    Smart night boost is not enabled
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Enable smart night boost in the Settings tab to start collecting learning data.
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      The adaptive learning system will automatically track heating cycles and improve predictions over time.
                    </Typography>
                  </Box>
                </Box>
              )}
            </Paper>
          </Box>
        </TabPanel>
      </Box>
    </Box>
  )
}

export default ZoneDetail
