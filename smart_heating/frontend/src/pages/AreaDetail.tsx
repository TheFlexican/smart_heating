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
import PersonIcon from '@mui/icons-material/Person'
import HistoryIcon from '@mui/icons-material/History'
import SpeedIcon from '@mui/icons-material/Speed'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import ArticleIcon from '@mui/icons-material/Article'
import { useTranslation } from 'react-i18next'
import { Zone, WindowSensorConfig, PresenceSensorConfig, Device, GlobalPresets } from '../types'
import { 
  getZones, 
  setZoneTemperature, 
  enableZone, 
  disableZone, 
  setPresetMode,
  setBoostMode,
  cancelBoost,
  setHvacMode,
  setSwitchShutdown,
  addWindowSensor,
  removeWindowSensor,
  addPresenceSensor,
  removePresenceSensor,
  getHistoryConfig,
  setHistoryRetention,
  getDevices,
  addDeviceToZone,
  removeDeviceFromZone,
  getEntityState,
  getGlobalPresets,
  setAreaPresetConfig,
  setAreaPresenceConfig,
  getAreaLogs,
  AreaLogEntry
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
      {value === index && <Box sx={{ p: { xs: 2, sm: 3 } }}>{children}</Box>}
    </div>
  )
}

const ZoneDetail = () => {
  const { t } = useTranslation()
  const { areaId } = useParams<{ areaId: string }>()
  const navigate = useNavigate()
  const [area, setZone] = useState<Zone | null>(null)
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [showOnlyHeating, setShowOnlyHeating] = useState(true)
  const [deviceSearch, setDeviceSearch] = useState('')
  const [entityStates, setEntityStates] = useState<Record<string, any>>({})
  const [globalPresets, setGlobalPresets] = useState<GlobalPresets | null>(null)
  const [loading, setLoading] = useState(true)
  const [tabValue, setTabValue] = useState(0)
  const [temperature, setTemperature] = useState(21)
  const [historyRetention, setHistoryRetentionState] = useState(30)
  const [recordInterval, setRecordInterval] = useState(5)
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [sensorDialogType, setSensorDialogType] = useState<'window' | 'presence'>('window')
  const [expandedCard, setExpandedCard] = useState<string | null>(null) // Accordion state
  const [logs, setLogs] = useState<AreaLogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')

  // WebSocket for real-time updates
  useWebSocket({
    onZoneUpdate: (updatedZone) => {
      if (updatedZone.id === areaId) {
        setZone(updatedZone)
        const displayTemp = (updatedZone.preset_mode && updatedZone.preset_mode !== 'none' && updatedZone.effective_target_temperature != null)
          ? updatedZone.effective_target_temperature
          : updatedZone.target_temperature
        setTemperature(displayTemp)
      }
    },
    onZonesUpdate: (areas) => {
      const currentZone = areas.find(z => z.id === areaId)
      if (currentZone) {
        setZone(currentZone)
        const displayTemp = (currentZone.preset_mode && currentZone.preset_mode !== 'none' && currentZone.effective_target_temperature != null)
          ? currentZone.effective_target_temperature
          : currentZone.target_temperature
        setTemperature(displayTemp)
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
      // If preset is active, show effective temperature, otherwise base target
      const displayTemp = (currentZone.preset_mode && currentZone.preset_mode !== 'none' && currentZone.effective_target_temperature != null)
        ? currentZone.effective_target_temperature
        : currentZone.target_temperature
      setTemperature(displayTemp)
      
      // Load global presets for preset configuration section
      try {
        const presets = await getGlobalPresets()
        setGlobalPresets(presets)
      } catch (error) {
        console.error('Failed to load global presets:', error)
      }
      
      // Load entity states for presence/window sensors
      await loadEntityStates(currentZone)
      
      // Load available devices
      await loadAvailableDevices(currentZone)
    } catch (error) {
      console.error('Failed to load area:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const loadEntityStates = async (currentZone: Zone) => {
    try {
      const states: Record<string, any> = {}
      
      // Load presence sensor states and names
      if (currentZone.presence_sensors) {
        for (const sensor of currentZone.presence_sensors) {
          const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
          try {
            const state = await getEntityState(entity_id)
            states[entity_id] = state
          } catch (error) {
            console.error(`Failed to load state for ${entity_id}:`, error)
          }
        }
      }
      
      // Load window sensor states and names
      if (currentZone.window_sensors) {
        for (const sensor of currentZone.window_sensors) {
          const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
          try {
            const state = await getEntityState(entity_id)
            states[entity_id] = state
          } catch (error) {
            console.error(`Failed to load state for ${entity_id}:`, error)
          }
        }
      }
      
      setEntityStates(states)
    } catch (error) {
      console.error('Failed to load entity states:', error)
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

  const loadLogs = async () => {
    if (!areaId) return
    
    try {
      setLogsLoading(true)
      const options: any = { limit: 100 }
      if (logFilter !== 'all') {
        options.type = logFilter
      }
      const logsData = await getAreaLogs(areaId, options)
      setLogs(logsData)
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLogsLoading(false)
    }
  }

  // Load logs when tab is switched to Logs tab
  useEffect(() => {
    if (tabValue === 6) { // Logs tab index
      loadLogs()
    }
  }, [tabValue, logFilter])

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

    // Helper function to get effective preset temperature (global or custom)
    const getPresetTemp = (presetKey: string, customTemp: number | undefined, fallback: number): string => {
      const useGlobalKey = `use_global_${presetKey}` as keyof Zone
      const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true
      
      if (useGlobal && globalPresets) {
        const globalKey = `${presetKey}_temp` as keyof GlobalPresets
        return `${globalPresets[globalKey]}°C (global)`
      } else {
        return `${customTemp ?? fallback}°C (custom)`
      }
    }

    return [
      {
        id: 'preset-modes',
        title: t('settingsCards.presetModesTitle'),
        description: t('settingsCards.presetModesDescription'),
        icon: <BookmarkIcon />,
        badge: area.preset_mode !== 'none' ? area.preset_mode : undefined,
        defaultExpanded: false,
        content: (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t('settingsCards.currentPreset')}</InputLabel>
              <Select
                value={area.preset_mode || 'none'}
                label={t('settingsCards.currentPreset')}
                onChange={async (e) => {
                  try {
                    await setPresetMode(area.id, e.target.value)
                    loadData()
                  } catch (error) {
                    console.error('Failed to set preset mode:', error)
                  }
                }}
              >
                <MenuItem value="none">{t('settingsCards.presetNoneManual')}</MenuItem>
                <MenuItem value="away">{t('settingsCards.presetAwayTemp', { temp: getPresetTemp('away', area.away_temp, 16) })}</MenuItem>
                <MenuItem value="eco">{t('settingsCards.presetEcoTemp', { temp: getPresetTemp('eco', area.eco_temp, 18) })}</MenuItem>
                <MenuItem value="comfort">{t('settingsCards.presetComfortTemp', { temp: getPresetTemp('comfort', area.comfort_temp, 22) })}</MenuItem>
                <MenuItem value="home">{t('settingsCards.presetHomeTemp', { temp: getPresetTemp('home', area.home_temp, 21) })}</MenuItem>
                <MenuItem value="sleep">{t('settingsCards.presetSleepTemp', { temp: getPresetTemp('sleep', area.sleep_temp, 19) })}</MenuItem>
                <MenuItem value="activity">{t('settingsCards.presetActivityTemp', { temp: getPresetTemp('activity', area.activity_temp, 23) })}</MenuItem>
                <MenuItem value="boost">{t('settingsCards.presetBoost')}</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info">
              {t('settingsCards.currentPresetInfo', { preset: area.preset_mode || 'none' })}
            </Alert>
          </>
        )
      },
      {
        id: 'preset-config',
        title: t('settingsCards.presetTemperatureConfigTitle'),
        description: t('settingsCards.presetTemperatureConfigDescription'),
        icon: <BookmarkIcon />,
        defaultExpanded: false,
        content: (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {globalPresets && [
              { key: 'away', label: 'Away', global: globalPresets.away_temp, custom: area.away_temp },
              { key: 'eco', label: 'Eco', global: globalPresets.eco_temp, custom: area.eco_temp },
              { key: 'comfort', label: 'Comfort', global: globalPresets.comfort_temp, custom: area.comfort_temp },
              { key: 'home', label: 'Home', global: globalPresets.home_temp, custom: area.home_temp },
              { key: 'sleep', label: 'Sleep', global: globalPresets.sleep_temp, custom: area.sleep_temp },
              { key: 'activity', label: 'Activity', global: globalPresets.activity_temp, custom: area.activity_temp },
            ].map(preset => {
              const useGlobalKey = `use_global_${preset.key}` as keyof Zone
              const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true
              const effectiveTemp = useGlobal ? preset.global : preset.custom
              
              return (
                <Box key={preset.key}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={useGlobal}
                        onChange={async (e) => {
                          e.stopPropagation()
                          const newValue = e.target.checked
                          try {
                            await setAreaPresetConfig(area.id, { [useGlobalKey]: newValue })
                            await loadData()
                          } catch (error) {
                            console.error('Failed to update preset config:', error)
                            alert(`Failed to update preset: ${error}`)
                          }
                        }}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body1">
                          {useGlobal ? t('settingsCards.presetUseGlobal', { preset: preset.label }) : t('settingsCards.presetUseCustom', { preset: preset.label })}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {useGlobal 
                            ? t('settingsCards.usingGlobalSetting', { temp: preset.global })
                            : t('settingsCards.usingCustomSetting', { temp: preset.custom ?? 'not set' })
                          }
                        </Typography>
                      </Box>
                    }
                  />
                  {!useGlobal && (
                    <Alert severity="info" sx={{ mt: 1 }}>
                      {t('settingsCards.customTempInfo', { temp: effectiveTemp })}
                    </Alert>
                  )}
                </Box>
              )
            })}
            
            <Alert severity="info" sx={{ mt: 2 }}>
              {t('settingsCards.presetConfigInfo')}
            </Alert>
          </Box>
        )
      },
      {
        id: 'boost-mode',
        title: t('settingsCards.boostModeTitle'),
        description: t('settingsCards.boostModeDescription'),
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
        id: 'switch-control',
        title: t('settingsCards.switchPumpControlTitle'),
        description: t('settingsCards.switchPumpControlDescription'),
        icon: <PowerSettingsNewIcon />,
        badge: (area.shutdown_switches_when_idle ?? true) ? 'Auto Off' : 'Always On',
        defaultExpanded: false,
        content: (
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={area.shutdown_switches_when_idle ?? true}
                  onChange={async (e) => {
                    try {
                      await setSwitchShutdown(area.id, e.target.checked)
                      loadData()
                    } catch (error) {
                      console.error('Failed to update switch shutdown setting:', error)
                    }
                  }}
                />
              }
              label={t('settingsCards.shutdownSwitchesPumps')}
            />
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1, ml: 4 }}>
              {t('settingsCards.shutdownSwitchesDescription')}
            </Typography>
          </Box>
        )
      },
      {
        id: 'window-sensors',
        title: t('settingsCards.windowSensorsTitle'),
        description: t('settingsCards.windowSensorsDescription'),
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
        id: 'presence-config',
        title: t('settingsCards.presenceConfigTitle'),
        description: t('settingsCards.presenceConfigDescription'),
        icon: <SensorOccupiedIcon />,
        defaultExpanded: false,
        content: (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={area.use_global_presence ?? false}
                  onChange={async (e) => {
                    e.stopPropagation()
                    const newValue = e.target.checked
                    console.log('Setting use_global_presence to:', newValue)
                    try {
                      await setAreaPresenceConfig(area.id, newValue)
                      // Force reload to get updated data
                      await loadData()
                    } catch (error) {
                      console.error('Failed to update presence config:', error)
                      alert(`Failed to update presence config: ${error}`)
                    }
                  }}
                />
              }
              label={
                <Box>
                  <Typography variant="body1">
                    {area.use_global_presence ? t('settingsCards.useGlobalPresence') : t('settingsCards.useAreaSpecificSensors')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {area.use_global_presence 
                      ? t('settingsCards.useGlobalPresenceDescription')
                      : t('settingsCards.useAreaSpecificDescription')
                    }
                  </Typography>
                </Box>
              }
            />
            
            <Alert severity="info">
              {t('settingsCards.presenceToggleInfo')}
            </Alert>
          </Box>
        )
      },
      {
        id: 'presence-sensors',
        title: t('settingsCards.presenceSensorsTitle'),
        description: t('settingsCards.presenceSensorsDescription'),
        icon: <SensorOccupiedIcon />,
        badge: area.presence_sensors?.length || undefined,
        defaultExpanded: false,
        content: (
          <>
            {area.presence_sensors && area.presence_sensors.length > 0 ? (
              <List dense>
                {area.presence_sensors.map((sensor) => {
                  const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
                  
                  const entityState = entityStates[entity_id]
                  const friendlyName = entityState?.attributes?.friendly_name || entity_id
                  const state = entityState?.state || 'unknown'
                  const isAway = state === 'not_home' || state === 'off' || state === 'away'
                  const isActive = isAway || state === 'home' || state === 'on'
                  
                  return (
                    <ListItem
                      key={entity_id}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={async () => {
                            try {
                              await removePresenceSensor(area.id, entity_id)
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
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography>{friendlyName}</Typography>
                            {isActive && (
                              <Chip 
                                label={isAway ? t('settingsCards.awayChip') : t('settingsCards.homeChip')} 
                                size="small" 
                                color={isAway ? 'warning' : 'success'}
                                sx={{ height: '20px', fontSize: '0.7rem' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Typography component="span" variant="body2" color="text.secondary">
                            {t('settingsCards.presenceSensorDescription')}
                          </Typography>
                        }
                      />
                    </ListItem>
                  )
                })}
              </List>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                {t('settingsCards.noPresenceSensors')}
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
              {t('settingsCards.addPresenceSensor')}
            </Button>
          </>
        )
      },
      {
        id: 'auto-preset',
        title: t('settingsCards.autoPresetTitle'),
        description: t('settingsCards.autoPresetDescription'),
        icon: <PersonIcon />,
        badge: area.auto_preset_enabled ? 'AUTO' : 'OFF',
        defaultExpanded: false,
        content: (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="body1" color="text.primary">
                  {t('settingsCards.enableAutoPreset')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('settingsCards.enableAutoPresetDescription')}
                </Typography>
              </Box>
              <Switch
                checked={area.auto_preset_enabled ?? false}
                onChange={async (e) => {
                  try {
                    await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        enabled: e.target.checked
                      })
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update auto preset:', error)
                  }
                }}
              />
            </Box>

            {area.auto_preset_enabled && (
              <>
                <Alert severity="info" sx={{ mb: 3 }}>
                  {t('settingsCards.autoPresetExplanation')}
                </Alert>
                
                <Box sx={{ mb: 3 }}>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>{t('settingsCards.presetWhenHome')}</InputLabel>
                    <Select
                      value={area.auto_preset_home || 'home'}
                      label={t('settingsCards.presetWhenHome')}
                      onChange={async (e) => {
                        try {
                          await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              enabled: true,
                              home_preset: e.target.value
                            })
                          })
                          loadData()
                        } catch (error) {
                          console.error('Failed to update home preset:', error)
                        }
                      }}
                    >
                      <MenuItem value="home">{t('settingsCards.presetHome')}</MenuItem>
                      <MenuItem value="comfort">{t('settingsCards.presetComfort')}</MenuItem>
                      <MenuItem value="activity">{t('settingsCards.presetActivity')}</MenuItem>
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>{t('settingsCards.presetWhenAway')}</InputLabel>
                    <Select
                      value={area.auto_preset_away || 'away'}
                      label={t('settingsCards.presetWhenAway')}
                      onChange={async (e) => {
                        try {
                          await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              enabled: true,
                              away_preset: e.target.value
                            })
                          })
                          loadData()
                        } catch (error) {
                          console.error('Failed to update away preset:', error)
                        }
                      }}
                    >
                      <MenuItem value="away">{t('settingsCards.presetAway')}</MenuItem>
                      <MenuItem value="eco">{t('settingsCards.presetEco')}</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </>
            )}

            {!area.auto_preset_enabled && (
              <Alert severity="warning">
                {t('settingsCards.autoPresetDisabled')}
              </Alert>
            )}

            {(!area.presence_sensors || area.presence_sensors.length === 0) && !area.use_global_presence && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                {t('settingsCards.autoPresetNeedsSensors')}
              </Alert>
            )}
          </>
        )
      },
      {
        id: 'night-boost',
        title: t('settingsCards.nightBoostTitle'),
        description: t('settingsCards.nightBoostDescription'),
        icon: <NightsStayIcon />,
        badge: area.night_boost_enabled ? 'ON' : 'OFF',
        defaultExpanded: false,
        content: (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="body1" color="text.primary">
                  {t('settingsCards.enableNightBoost')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('settingsCards.enableNightBoostDescription')}
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
              {t('settingsCards.nightBoostPeriod')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                label={t('settingsCards.startTime')}
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
                label={t('settingsCards.endTime')}
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
              {t('settingsCards.nightBoostOffset')}
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
        title: t('settingsCards.smartNightBoostTitle'),
        description: t('settingsCards.smartNightBoostDescription'),
        icon: <PsychologyIcon />,
        badge: area.smart_night_boost_enabled ? 'LEARNING' : 'OFF',
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('settingsCards.smartNightBoostIntro')}
            </Typography>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="body1" color="text.primary">
                  {t('settingsCards.enableSmartNightBoost')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('settingsCards.enableSmartNightBoostDescription')}
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
              label={t('settingsCards.targetWakeupTime')}
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
              helperText={t('settingsCards.targetWakeupTimeHelper')}
              InputLabelProps={{ shrink: true }}
              inputProps={{ step: 300 }}
              sx={{ mb: 3 }}
            />

            <TextField
              label={t('settingsCards.outdoorTemperatureSensor')}
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
              placeholder={t('settingsCards.outdoorTemperatureSensorPlaceholder')}
              helperText={t('settingsCards.outdoorTemperatureSensorHelper')}
            />

            {area.smart_night_boost_enabled && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>{t('settingsCards.smartNightBoostHowItWorksTitle')}</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary" component="div">
                  • {t('settingsCards.smartNightBoostBullet1')}<br/>
                  • {t('settingsCards.smartNightBoostBullet2')}<br/>
                  • {t('settingsCards.smartNightBoostBullet3')}<br/>
                  • {t('settingsCards.smartNightBoostBullet4')}
                </Typography>
              </Box>
            )}
          </>
        )
      },
      {
        id: 'heating-control',
        title: t('settingsCards.heatingControlTitle'),
        description: t('settingsCards.heatingControlDescription'),
        icon: <TuneIcon />,
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('settingsCards.temperatureHysteresis')}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              {t('settingsCards.temperatureHysteresisDescription')}
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={area.hysteresis_override === null || area.hysteresis_override === undefined}
                  onChange={async (e) => {
                    const useGlobal = e.target.checked
                    
                    // Optimistic update
                    const updatedArea = {
                      ...area,
                      hysteresis_override: useGlobal ? null : 0.5
                    }
                    setZone(updatedArea)
                    
                    try {
                      const response = await fetch(`/api/smart_heating/areas/${area.id}/hysteresis`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          use_global: useGlobal,
                          hysteresis: useGlobal ? null : 0.5
                        })
                      })
                      if (!response.ok) {
                        const errorText = await response.text()
                        console.error('Failed to update hysteresis setting:', errorText)
                        // Revert on error
                        setZone(area)
                      }
                    } catch (error) {
                      console.error('Failed to update hysteresis setting:', error)
                      // Revert on error
                      setZone(area)
                    }
                  }}
                />
              }
              label={t('settingsCards.useGlobalHysteresis')}
              sx={{ mb: 2 }}
            />
            
            {(area.hysteresis_override === null || area.hysteresis_override === undefined) ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                {t('settingsCards.usingGlobalHysteresis')}
              </Alert>
            ) : (
              <>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {t('settingsCards.usingAreaHysteresis')}
                </Alert>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
                  <Slider
                    value={area.hysteresis_override || 0.5}
                    onChange={async (_e, value) => {
                      // Optimistic update
                      const updatedArea = {
                        ...area,
                        hysteresis_override: typeof value === 'number' ? value : 0.5
                      }
                      setZone(updatedArea)
                      
                      try {
                        const response = await fetch(`/api/smart_heating/areas/${area.id}/hysteresis`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            use_global: false,
                            hysteresis: value
                          })
                        })
                        if (!response.ok) {
                          const errorText = await response.text()
                          console.error('Failed to update hysteresis:', errorText)
                          // Revert on error
                          setZone(area)
                        }
                      } catch (error) {
                        console.error('Failed to update hysteresis:', error)
                        // Revert on error
                        setZone(area)
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
                    valueLabelDisplay="on"
                    valueLabelFormat={(value) => `${value}°C`}
                    sx={{ flexGrow: 1 }}
                  />
                </Box>
              </>
            )}

            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('settingsCards.temperatureLimits')}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              {t('settingsCards.temperatureLimitsDescription')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('settingsCards.minimumTemperature')}
                </Typography>
                <Typography variant="h4" color="text.primary">
                  5°C
                </Typography>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('settingsCards.maximumTemperature')}
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
        title: t('settingsCards.historyManagementTitle'),
        description: t('settingsCards.historyManagementDescription'),
        icon: <HistoryIcon />,
        defaultExpanded: false,
        content: (
          <>
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('settingsCards.dataRetentionDescription', { interval: recordInterval })}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {t('settingsCards.dataRetentionPeriod', { days: historyRetention })}
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
                {t('common.save')}
              </Button>
            </Box>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <strong>Note:</strong> {t('settingsCards.historyNote', { interval: recordInterval })}
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
          p: { xs: 1.5, sm: 2 },
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 } }}>
            <IconButton onClick={() => navigate('/')} edge="start" sx={{ p: { xs: 0.5, sm: 1 } }}>
              <ArrowBackIcon />
            </IconButton>
            <Box>
              <Typography variant="h5" color="text.primary" sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                {area.name}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                <Chip
                  label={area.state.toUpperCase()}
                  color={getStateColor(area.state)}
                  size="small"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
                />
                <Chip
                  label={area.enabled ? 'ENABLED' : 'DISABLED'}
                  color={area.enabled ? 'success' : 'default'}
                  size="small"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
                />
              </Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, alignItems: 'center', mr: { xs: 0, sm: 2 } }}>
            <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
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
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              minWidth: { xs: 'auto', sm: 160 },
              px: { xs: 1, sm: 2 }
            }
          }}
        >
          <Tab label={t('tabs.overview')} />
          <Tab label={t('tabs.devices')} />
          <Tab label={t('tabs.schedule')} />
          <Tab label={t('tabs.history')} />
          <Tab label={t('tabs.settings')} />
          <Tab label={t('tabs.learning')} />
          <Tab label={t('tabs.logs')} icon={<ArticleIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ maxWidth: 800, mx: 'auto', px: { xs: 0, sm: 0 } }}>
            <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary" sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                {t('areaDetail.temperatureControl')}
              </Typography>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {t('areaDetail.targetTemperature')}
                </Typography>
                <Typography variant="h4" color="primary" sx={{ fontSize: { xs: '1.75rem', sm: '2.125rem' } }}>
                  {temperature}°C
                </Typography>
              </Box>
              <Slider
                value={temperature}
                sx={{
                  '& .MuiSlider-thumb': {
                    width: { xs: 24, sm: 20 },
                    height: { xs: 24, sm: 20 },
                  },
                  '& .MuiSlider-track': {
                    height: { xs: 6, sm: 4 },
                  },
                  '& .MuiSlider-rail': {
                    height: { xs: 6, sm: 4 },
                  },
                }}

                onChange={handleTemperatureChange}
                onChangeCommitted={handleTemperatureCommit}
                min={5}
                max={30}
                step={0.1}
                marks={[
                  { value: 5, label: '5°' },
                  { value: 15, label: '15°' },
                  { value: 20, label: '20°' },
                  { value: 25, label: '25°' },
                  { value: 30, label: '30°' }
                ]}
                valueLabelDisplay="auto"
                disabled={!area.enabled || !!(area.preset_mode && area.preset_mode !== 'none')}
              />
              {area.preset_mode && area.preset_mode !== 'none' && (
                <Box mt={1} display="flex" alignItems="center" gap={1}>
                  <BookmarkIcon fontSize="small" color="secondary" />
                  <Typography variant="caption" color="text.secondary" dangerouslySetInnerHTML={{
                    __html: t('areaDetail.presetModeActive', { mode: area.preset_mode.toUpperCase() })
                  }} />
                </Box>
              )}

              {area.current_temperature !== undefined && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body1" color="text.secondary">
                      {t('areaDetail.currentTemperature')}
                    </Typography>
                    <Typography variant="h5" color="text.primary">
                      {area.current_temperature?.toFixed(1)}°C
                    </Typography>
                  </Box>
                </>
              )}
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                {t('areaDetail.quickStats')}
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary={t('areaDetail.devices')}
                    secondary={t('areaDetail.devicesAssigned', { count: area.devices.length })}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary={t('areaDetail.status')}
                    secondary={area.state}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary={t('areaDetail.zoneId')}
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
                {t('areaDetail.assignedDevices', { count: area.devices.length })}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('areaDetail.devicesDescription')}
              </Typography>

              {area.devices.length === 0 ? (
                <Alert severity="info">
                  {t('areaDetail.noDevicesAssigned')}
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
                  {t('areaDetail.availableDevices', { count: availableDevices.filter(device => {
                    const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                    if (!deviceSearch) return typeMatch
                    const searchLower = deviceSearch.toLowerCase()
                    const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                    const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
                    const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                    return typeMatch && (nameMatch || entityMatch || areaMatch)
                  }).length })}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showOnlyHeating}
                      onChange={(e) => setShowOnlyHeating(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={t('areaDetail.showOnlyClimate')}
                />
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('areaDetail.availableDevicesDescription', { area: area.name })}
              </Typography>

              {/* Search Bar */}
              <TextField
                fullWidth
                size="small"
                placeholder={t('areaDetail.searchPlaceholder')}
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
                    ? t('areaDetail.noDevicesMatch', { search: deviceSearch })
                    : showOnlyHeating 
                      ? t('areaDetail.noClimateDevices')
                      : t('areaDetail.noAdditionalDevices')}
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
                {t('areaDetail.temperatureHistory')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('areaDetail.historyDescription')}
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
                {t('areaDetail.adaptiveLearning')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('areaDetail.learningDescription')}
              </Typography>

              {area.smart_night_boost_enabled ? (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="success.main" gutterBottom>
                    ✓ {t('areaDetail.smartNightBoostActive')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 3 }}>
                    {t('areaDetail.learningSystemText')}
                  </Typography>

                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, mb: 3 }}>
                    <Typography variant="body2" color="info.dark">
                      <strong>Note:</strong> {t('areaDetail.learningNote')}
                    </Typography>
                  </Box>

                  <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
                    {t('areaDetail.configuration')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">{t('areaDetail.targetWakeupTime')}</Typography>
                      <Typography variant="body2" color="text.primary"><strong>{area.smart_night_boost_target_time ?? '06:00'}</strong></Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">{t('areaDetail.weatherSensor')}</Typography>
                      <Typography variant="body2" color="text.primary">
                        {area.weather_entity_id ? <strong>{area.weather_entity_id}</strong> : <em>{t('areaDetail.notConfigured')}</em>}
                      </Typography>
                    </Box>
                  </Box>

                  <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
                    {t('areaDetail.learningProcessTitle')}
                  </Typography>
                  <Box component="ol" sx={{ pl: 2, mt: 1 }}>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {t('settingsCards.learningStep1')}
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {t('settingsCards.learningStep2')}
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {t('settingsCards.learningStep3')}
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {t('settingsCards.learningStep4')}
                    </Typography>
                    <Typography component="li" variant="body2" color="text.secondary">
                      {t('settingsCards.learningStep5')}
                    </Typography>
                  </Box>

                  <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>{t('areaDetail.apiEndpointLabel')}</strong> /api/smart_heating/areas/{area.id}/learning
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ mt: 3, textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    {t('settingsCards.smartNightBoostNotEnabled')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {t('settingsCards.enableSmartNightBoostInfo')}
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {t('settingsCards.adaptiveLearningInfo')}
                    </Typography>
                  </Box>
                </Box>
              )}
            </Paper>
          </Box>
        </TabPanel>

        {/* Logs Tab */}
        <TabPanel value={tabValue} index={6}>
          <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" color="text.primary">
                  {t('areaDetail.heatingStrategyLogs')}
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  onClick={loadLogs}
                  disabled={logsLoading}
                >
                  {logsLoading ? 'Loading...' : t('areaDetail.refresh')}
                </Button>
              </Box>

              <Typography variant="body2" color="text.secondary" paragraph>
                {t('areaDetail.logsDescription')}
              </Typography>

              <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={t('areaDetail.allEvents')}
                  onClick={() => setLogFilter('all')}
                  color={logFilter === 'all' ? 'primary' : 'default'}
                  variant={logFilter === 'all' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.temperature')}
                  onClick={() => setLogFilter('temperature')}
                  color={logFilter === 'temperature' ? 'info' : 'default'}
                  variant={logFilter === 'temperature' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.heating')}
                  onClick={() => setLogFilter('heating')}
                  color={logFilter === 'heating' ? 'error' : 'default'}
                  variant={logFilter === 'heating' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.schedule')}
                  onClick={() => setLogFilter('schedule')}
                  color={logFilter === 'schedule' ? 'success' : 'default'}
                  variant={logFilter === 'schedule' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.smartBoost')}
                  onClick={() => setLogFilter('smart_boost')}
                  color={logFilter === 'smart_boost' ? 'secondary' : 'default'}
                  variant={logFilter === 'smart_boost' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.sensors')}
                  onClick={() => setLogFilter('sensor')}
                  color={logFilter === 'sensor' ? 'warning' : 'default'}
                  variant={logFilter === 'sensor' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
                <Chip
                  label={t('areaDetail.mode')}
                  onClick={() => setLogFilter('mode')}
                  color={logFilter === 'mode' ? 'primary' : 'default'}
                  variant={logFilter === 'mode' ? 'filled' : 'outlined'}
                  sx={{ cursor: 'pointer' }}
                />
              </Box>

              {logsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : logs.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('settingsCards.noLogsYet')}
                  </Typography>
                </Box>
              ) : (
                <List sx={{ bgcolor: 'background.paper' }}>
                  {logs.map((log, index) => {
                    const timestamp = new Date(log.timestamp)
                    const timeStr = timestamp.toLocaleTimeString('nl-NL', { 
                      hour: '2-digit', 
                      minute: '2-digit',
                      second: '2-digit'
                    })
                    const dateStr = timestamp.toLocaleDateString('nl-NL')
                    
                    // Color coding by event type
                    const getEventColor = (type: string) => {
                      switch (type) {
                        case 'heating': return 'error'
                        case 'temperature': return 'info'
                        case 'schedule': return 'success'
                        case 'smart_boost': return 'secondary'
                        case 'sensor': return 'warning'
                        case 'mode': return 'primary'
                        default: return 'default'
                      }
                    }
                    
                    return (
                      <Box key={index}>
                        {index > 0 && <Divider />}
                        <ListItem alignItems="flex-start" sx={{ py: 2 }}>
                          <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                            <Chip 
                              label={log.type} 
                              color={getEventColor(log.type)}
                              size="small"
                              sx={{ fontSize: '0.7rem', height: 20 }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Typography variant="body2" color="text.primary">
                                  {log.message}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                                  {dateStr} {timeStr}
                                </Typography>
                              </Box>
                            }
                            secondary={
                              log.details && Object.keys(log.details).length > 0 && (
                                <Box 
                                  component="pre" 
                                  sx={{ 
                                    mt: 1, 
                                    p: 1, 
                                    bgcolor: 'action.hover', 
                                    borderRadius: 1,
                                    fontSize: '0.75rem',
                                    overflow: 'auto',
                                    fontFamily: 'monospace'
                                  }}
                                >
                                  {JSON.stringify(log.details, null, 2)}
                                </Box>
                              )
                            }
                          />
                        </ListItem>
                      </Box>
                    )
                  })}
                </List>
              )}
            </Paper>
          </Box>
        </TabPanel>
      </Box>
    </Box>
  )
}

export default ZoneDetail
