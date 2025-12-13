import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Slider,
  IconButton,
  Alert,
  CircularProgress,
  Stack,
  Button,
  List,
  ListItem,
  ListItemText,
  Tabs,
  Tab,
  Switch,
  // TextField no longer used in this file
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  // FormControlLabel removed - no enable toggle for OpenTherm
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import PeopleIcon from '@mui/icons-material/People'
import BeachAccessIcon from '@mui/icons-material/BeachAccess'
import TuneIcon from '@mui/icons-material/Tune'
import SecurityIcon from '@mui/icons-material/Security'
import BackupIcon from '@mui/icons-material/Backup'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import AssessmentIcon from '@mui/icons-material/Assessment'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getGlobalPresets, setGlobalPresets, getGlobalPresence, setGlobalPresence, getHysteresis, setHysteresis, getSafetySensor, setSafetySensor, removeSafetySensor, setHideDevicesPanel, getConfig, setOpenthermGateway, getOpenthermGateways, getAdvancedControlConfig, setAdvancedControlConfig, calibrateOpentherm, type SafetySensorResponse } from '../api'
import { PresenceSensorConfig, WindowSensorConfig, SafetySensorConfig } from '../types'
import SensorConfigDialog from '../components/SensorConfigDialog'
import SafetySensorConfigDialog from '../components/SafetySensorConfigDialog'
import { VacationModeSettings } from '../components/VacationModeSettings'
import HysteresisHelpModal from '../components/HysteresisHelpModal'
import ImportExport from '../components/ImportExport'
import OpenThermLogger from '../components/OpenThermLogger'
// additional advanced control apis already imported above

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

interface GlobalPresetsData {
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}

const presetLabels = {
  away_temp: 'Away',
  eco_temp: 'Eco',
  comfort_temp: 'Comfort',
  home_temp: 'Home',
  sleep_temp: 'Sleep',
  activity_temp: 'Activity',
}

const presetDescriptions = {
  away_temp: 'Used when nobody is home',
  eco_temp: 'Energy-saving temperature',
  comfort_temp: 'Comfortable temperature for relaxing',
  home_temp: 'Standard temperature when home',
  sleep_temp: 'Nighttime sleeping temperature',
  activity_temp: 'Active daytime temperature',
}

export default function GlobalSettings({ themeMode, onThemeChange }: { themeMode: 'light' | 'dark', onThemeChange: (mode: 'light' | 'dark') => void }) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState(0)
  const [presets, setPresets] = useState<GlobalPresetsData | null>(null)
  const [hysteresis, setHysteresisValue] = useState<number>(0.5)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveTimeout, setSaveTimeout] = useState<number | null>(null)
  const [hysteresisSaveTimeout, setHysteresisSaveTimeout] = useState<number | null>(null)
  const [presenceSensors, setPresenceSensors] = useState<PresenceSensorConfig[]>([])
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [hysteresisHelpOpen, setHysteresisHelpOpen] = useState(false)
  const [safetySensor, setSafetySensorState] = useState<SafetySensorResponse | null>(null)
  const [safetySensorDialogOpen, setSafetySensorDialogOpen] = useState(false)
  const [hideDevicesPanel, setHideDevicesPanelState] = useState(false)
  // Advanced control state
  const [advancedControlEnabled, setAdvancedControlEnabled] = useState(false)
  const [heatingCurveEnabled, setHeatingCurveEnabled] = useState(false)
  const [pwmEnabled, setPwmEnabled] = useState(false)
  const [pidEnabled, setPidEnabled] = useState(false)
  const [overshootProtectionEnabled, setOvershootProtectionEnabled] = useState(false)
  const [defaultCoefficient, setDefaultCoefficient] = useState<number>(1.0)

  // OpenTherm Gateway Configuration
  const [openthermGatewayId, setOpenthermGatewayId] = useState<string>('')
  const [openthermSaving, setOpenthermSaving] = useState(false)
  const [openthermGateways, setOpenthermGateways] = useState<Array<{gateway_id: string, title: string}>>([])

  useEffect(() => {
    loadPresets()
    loadHysteresis()
    loadPresenceSensors()
    loadSafetySensor()
    loadConfig()
    loadOpenthermGateways()
    loadAdvancedControlConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const config = await getConfig()
      setHideDevicesPanelState(config.hide_devices_panel || false)

      // Load OpenTherm configuration
      setOpenthermGatewayId(config.opentherm_gateway_id || '')
      setHideDevicesPanelState(config.hide_devices_panel || false)
    } catch (err) {
      console.error('Error loading config:', err)
    }
  }

  const loadAdvancedControlConfig = async () => {
    try {
      const cfg = await getAdvancedControlConfig()
      // cfg is a config block; it includes advanced control keys
      setAdvancedControlEnabled(!!cfg.advanced_control_enabled)
      setHeatingCurveEnabled(!!cfg.heating_curve_enabled)
      setPwmEnabled(!!cfg.pwm_enabled)
      setPidEnabled(!!cfg.pid_enabled)
      setOvershootProtectionEnabled(!!cfg.overshoot_protection_enabled)
      setDefaultCoefficient(Number(cfg.default_heating_curve_coefficient || 1.0))
    } catch (err) {
      console.error('Error loading advanced control config', err)
    }
  }

  const loadOpenthermGateways = async () => {
    try {
      const gateways = await getOpenthermGateways()
      setOpenthermGateways(gateways)
    } catch (err) {
      console.error('Error loading OpenTherm gateways:', err)
    }
  }

  const loadPresets = async () => {
    try {
      setLoading(true)
      const data = await getGlobalPresets()
      setPresets(data)
      setError(null)
    } catch (err) {
      setError('Failed to load global presets')
      console.error('Error loading global presets:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadPresenceSensors = async () => {
    try {
      const data = await getGlobalPresence()
      setPresenceSensors(data.sensors || [])
    } catch (err) {
      console.error('Error loading global presence sensors:', err)
    }
  }

  const loadHysteresis = async () => {
    try {
      const value = await getHysteresis()
      setHysteresisValue(value)
    } catch (err) {
      console.error('Error loading hysteresis:', err)
    }
  }

  const loadSafetySensor = async () => {
    try {
      const data = await getSafetySensor()
      setSafetySensorState(data)
    } catch (err) {
      console.error('Error loading safety sensor:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePresetChange = (key: keyof GlobalPresetsData, value: number) => {
    if (!presets) return

    const newPresets = { ...presets, [key]: value }
    setPresets(newPresets)

    // Clear any existing timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout)
    }

    // Set a new timeout to save after 500ms of no changes
    const timeout = setTimeout(async () => {
      try {
        setSaving(true)
        setSaveSuccess(false)
        await setGlobalPresets({ [key]: value })
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 2000)
      } catch (err) {
        setError('Failed to save preset')
        console.error('Error saving preset:', err)
        // Revert on error
        await loadPresets()
      } finally {
        setSaving(false)
      }
    }, 500)

    setSaveTimeout(timeout)
  }

  const handleHysteresisChange = (_event: Event, value: number | number[]) => {
    const newValue = Array.isArray(value) ? value[0] : value
    setHysteresisValue(newValue)

    // Clear any existing timeout
    if (hysteresisSaveTimeout) {
      clearTimeout(hysteresisSaveTimeout)
    }

    // Set a new timeout to save after 500ms of no changes
    const timeout = setTimeout(async () => {
      try {
        setSaving(true)
        setSaveSuccess(false)
        await setHysteresis(newValue)
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 2000)
      } catch (err) {
        setError('Failed to save hysteresis')
        console.error('Error saving hysteresis:', err)
        // Revert on error
        await loadHysteresis()
      } finally {
        setSaving(false)
      }
    }, 500)

    setHysteresisSaveTimeout(timeout)
  }

  const handleToggleHideDevicesPanel = async (hide: boolean) => {
    try {
      setHideDevicesPanelState(hide)
      await setHideDevicesPanel(hide)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
      // Reload to apply changes
      setTimeout(() => window.location.reload(), 500)
    } catch (err) {
      setError('Failed to save setting')
      console.error('Error saving hide devices panel:', err)
      setHideDevicesPanelState(!hide)
    }
  }

  const handleToggleAdvancedControl = async (field: string, value: boolean | number) => {
    const payload: any = {}
    payload[field] = value
    try {
      await setAdvancedControlConfig(payload)
      // Push local state update
      switch (field) {
        case 'advanced_control_enabled':
          setAdvancedControlEnabled(Boolean(value))
          break
        case 'heating_curve_enabled':
          setHeatingCurveEnabled(Boolean(value))
          break
        case 'pwm_enabled':
          setPwmEnabled(Boolean(value))
          break
        case 'pid_enabled':
          setPidEnabled(Boolean(value))
          break
        case 'overshoot_protection_enabled':
          setOvershootProtectionEnabled(Boolean(value))
          break
        case 'default_heating_curve_coefficient':
          setDefaultCoefficient(Number(value))
          break
      }
    } catch (err) {
      setError('Failed to save advanced control setting')
      console.error('Error saving advanced control setting:', err)
    }
  }

  const handleResetAdvancedControl = async () => {
    try {
      setSaving(true)
      // Reset to sensible defaults
      await setAdvancedControlConfig({
        advanced_control_enabled: false,
        heating_curve_enabled: false,
        pwm_enabled: false,
        pid_enabled: false,
        overshoot_protection_enabled: false,
        default_heating_curve_coefficient: 1.0,
      })
      // reload values immediately
      await loadAdvancedControlConfig()
    } catch (err) {
      setError('Failed to reset advanced control settings')
      console.error('Error resetting advanced control:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveOpenthermConfig = async () => {
    try {
      setOpenthermSaving(true)
      // Only send gateway id; control is automatic when a gateway is configured
      await setOpenthermGateway(openthermGatewayId)
      // Reload config to confirm saved values
      await loadConfig()
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      setError('Failed to save OpenTherm configuration')
      console.error('Error saving OpenTherm config:', err)
    } finally {
      setOpenthermSaving(false)
    }
  }
  const [calibrating, setCalibrating] = useState(false)
  const [calibrationResult, setCalibrationResult] = useState<number | null>(null)

  const handleRunCalibration = async () => {
    setCalibrating(true)
    try {
      const res = await calibrateOpentherm()
      if (res && res.opv) {
        setCalibrationResult(res.opv)
      }
    } catch (err) {
      setError('Calibration failed')
      console.error('Calibration error:', err)
    } finally {
      setCalibrating(false)
    }
  }

  const handleAddPresenceSensor = async (config: WindowSensorConfig | PresenceSensorConfig) => {
    try {
      const newSensors = [...presenceSensors, config as PresenceSensorConfig]
      await setGlobalPresence(newSensors)
      await loadPresenceSensors()
      setSensorDialogOpen(false)
    } catch (err) {
      console.error('Error adding presence sensor:', err)
      setError('Failed to add presence sensor')
    }
  }

  const handleRemovePresenceSensor = async (entityId: string) => {
    try {
      const newSensors = presenceSensors.filter(s => s.entity_id !== entityId)
      await setGlobalPresence(newSensors)
      await loadPresenceSensors()
    } catch (err) {
      console.error('Error removing presence sensor:', err)
      setError('Failed to remove presence sensor')
    }
  }

  const handleAddSafetySensor = async (config: SafetySensorConfig) => {
    try {
      await setSafetySensor(config)
      await loadSafetySensor()
      setSafetySensorDialogOpen(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      console.error('Error adding safety sensor:', err)
      setError('Failed to add safety sensor')
    }
  }

  const handleRemoveSafetySensor = async (sensorId: string) => {
    try {
      await removeSafetySensor(sensorId)
      await loadSafetySensor()
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      console.error('Error removing safety sensor:', err)
      setError('Failed to remove safety sensor')
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error && !presets) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', pb: 0, display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 2,
          borderRadius: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <IconButton onClick={() => navigate('/')} edge="start">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6">{t('globalSettings.title', 'Global Settings')}</Typography>
      </Paper>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          aria-label="global settings tabs"
        >
          {/* Removed duplicate Advanced Control tab to keep tabs in the correct order */}
          <Tab
            icon={<ThermostatIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.temperature', 'Temperature')}
          />
          <Tab
            icon={<PeopleIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.sensors', 'Sensors')}
          />
          <Tab
            icon={<BeachAccessIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.vacation', 'Vacation')}
          />
          <Tab
            icon={<SecurityIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.safety', 'Safety')}
          />
          <Tab
            icon={<TuneIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.advanced', 'Advanced')}
          />
          <Tab
            icon={<BackupIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.importExport', 'Import/Export')}
          />
          <Tab
            icon={<FireplaceIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.opentherm', 'OpenTherm')}
          />
        </Tabs>
      </Box>

      {/* Content area: on mobile allow scrolling inside the viewport */}
      <Box sx={{ px: 2, overflowY: { xs: 'auto', sm: 'visible' }, maxHeight: { xs: 'calc(100vh - 120px)', sm: 'none' }, py: 2 }}>
        {saveSuccess && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            {t('globalSettings.saveSuccess', 'Settings saved successfully')}
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Temperature Tab */}
        <TabPanel value={activeTab} index={0}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('globalSettings.presets.title', 'Preset Temperatures')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {t('globalSettings.presets.description', 'These are the default temperatures for each preset mode. Areas can choose to use these global settings or define their own custom temperatures.')}
            </Typography>

            <Stack spacing={3}>
              {presets && Object.entries(presetLabels).map(([key, label]) => {
                const presetKey = key as keyof GlobalPresetsData
                const value = presets[presetKey]

                return (
                  <Box key={key}>
                    <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                      {label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {presetDescriptions[presetKey]}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
                      <Slider
                        value={value}
                        onChange={(_, newValue) => handlePresetChange(presetKey, newValue as number)}
                        min={5}
                        max={30}
                        step={0.1}
                        marks={[
                          { value: 5, label: '5°C' },
                          { value: 15, label: '15°C' },
                          { value: 20, label: '20°C' },
                          { value: 25, label: '25°C' },
                          { value: 30, label: '30°C' },
                        ]}
                        valueLabelDisplay="on"
                        valueLabelFormat={(v) => `${v}°C`}
                        disabled={saving}
                        sx={{ maxWidth: 600 }}
                      />
                    </Box>
                  </Box>
                )
              })}
            </Stack>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
              💡 {t('globalSettings.presets.tip', 'Tip: To customize temperatures for a specific area, go to that area\'s settings and toggle off "Use global preset" for individual preset modes.')}
            </Typography>
          </Paper>
        </TabPanel>

        {/* Sensors Tab */}
        <TabPanel value={activeTab} index={1}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('globalSettings.sensors.title', 'Global Presence Sensors')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {t('globalSettings.sensors.description', 'Configure presence sensors that can be used across all areas. Areas can choose to use these global sensors or configure their own.')}
            </Typography>

            {presenceSensors.length > 0 ? (
              <List dense>
                {presenceSensors.map((sensor) => (
                  <ListItem
                    key={sensor.entity_id}
                    secondaryAction={
                      <IconButton
                        edge="end"
                        onClick={() => handleRemovePresenceSensor(sensor.entity_id)}
                      >
                        <RemoveCircleOutlineIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={sensor.entity_id}
                      secondary={t('globalSettings.sensors.switchText', 'Switches heating to \'away\' when nobody is home')}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                {t('globalSettings.sensors.noSensors', 'No global presence sensors configured. Add sensors that will be available to all areas.')}
              </Alert>
            )}

            <Button
              variant="outlined"
              fullWidth
              onClick={() => setSensorDialogOpen(true)}
              sx={{ mt: 2 }}
            >
              {t('globalSettings.sensors.addButton', 'Add Presence Sensor')}
            </Button>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
              💡 {t('globalSettings.sensors.tip', 'Tip: Areas can enable "Use global presence" in their settings to use these sensors instead of configuring their own.')}
            </Typography>
          </Paper>
        </TabPanel>

        {/* Vacation Tab */}
        <TabPanel value={activeTab} index={2}>
          <VacationModeSettings />
        </TabPanel>

        {/* Safety Tab */}
        <TabPanel value={activeTab} index={3}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('globalSettings.safety.title', '🚨 Safety Sensors (Smoke/CO Detectors)')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {t('globalSettings.safety.description', 'Configure smoke or carbon monoxide detectors that will automatically shut down all heating when danger is detected. All areas will be disabled immediately to prevent heating during a safety emergency.')}
            </Typography>

            {safetySensor?.alert_active && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {t('globalSettings.safety.alertActive', '⚠️ SAFETY ALERT ACTIVE! All heating has been shut down. Please resolve the safety issue and manually re-enable areas.')}
              </Alert>
            )}

            {safetySensor?.sensors && safetySensor.sensors.length > 0 ? (
              <>
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                    {t('globalSettings.safety.configured', 'Safety Sensors Configured')} ({safetySensor.sensors.length})
                  </Typography>
                </Alert>

                <List sx={{ mb: 2 }}>
                  {safetySensor.sensors.map((sensor) => (
                    <ListItem
                      key={sensor.sensor_id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          aria-label="delete"
                          onClick={() => handleRemoveSafetySensor(sensor.sensor_id)}
                          color="error"
                        >
                          <RemoveCircleOutlineIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={sensor.sensor_id}
                        secondary={
                          <>
                            <Typography component="span" variant="body2">
                              {t('globalSettings.safety.attribute', 'Attribute')}: {sensor.attribute} | {' '}
                              {t('globalSettings.safety.status', 'Status')}: {
                                sensor.enabled
                                  ? t('globalSettings.safety.enabled', '✓ Enabled')
                                  : t('globalSettings.safety.disabled', '✗ Disabled')
                              }
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setSafetySensorDialogOpen(true)}
                  startIcon={<SecurityIcon />}
                  sx={{ mb: 2 }}
                >
                  {t('globalSettings.safety.addAnotherButton', 'Add Another Safety Sensor')}
                </Button>
              </>
            ) : (
              <>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {t('globalSettings.safety.notConfigured', 'No safety sensors configured. It is highly recommended to configure smoke or CO detectors for emergency heating shutdown.')}
                </Alert>

                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => setSafetySensorDialogOpen(true)}
                  startIcon={<SecurityIcon />}
                >
                  {t('globalSettings.safety.addButton', 'Add Safety Sensor')}
                </Button>
              </>
            )}

            <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
              💡 {t('globalSettings.safety.tip', 'When any safety sensor detects smoke or carbon monoxide, all heating will be immediately stopped and all areas disabled. Areas must be manually re-enabled after the safety issue is resolved.')}
            </Typography>
          </Paper>
        </TabPanel>

        {/* Advanced Tab */}
        <TabPanel value={activeTab} index={4}>
          {/* Theme Settings */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('globalSettings.theme.title', 'Theme')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {t('globalSettings.theme.description', 'Choose the color theme for the application interface.')}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="subtitle1">
                  {t('globalSettings.theme.mode', 'Appearance')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {themeMode === 'dark'
                    ? t('globalSettings.theme.darkMode', 'Dark mode is active')
                    : t('globalSettings.theme.lightMode', 'Light mode is active')}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" color={themeMode === 'light' ? 'primary' : 'text.secondary'}>
                  {t('globalSettings.theme.light', 'Light')}
                </Typography>
                <Switch
                  checked={themeMode === 'dark'}
                  onChange={(e) => onThemeChange(e.target.checked ? 'dark' : 'light')}
                  color="primary"
                />
                <Typography variant="body2" color={themeMode === 'dark' ? 'primary' : 'text.secondary'}>
                  {t('globalSettings.theme.dark', 'Dark')}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Temperature Hysteresis */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="h6">
                {t('globalSettings.hysteresis.title', 'Temperature Hysteresis')}
              </Typography>
              <IconButton
                onClick={() => setHysteresisHelpOpen(true)}
                color="primary"
                size="small"
              >
                <HelpOutlineIcon />
              </IconButton>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('globalSettings.hysteresis.description', 'Controls the temperature buffer to prevent rapid on/off cycling of your heating system.')}
            </Typography>

            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>{t('globalSettings.hysteresis.what', 'What is hysteresis?')}</strong>
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {t('globalSettings.hysteresis.explanation', 'Hysteresis prevents your heating system from constantly turning on and off (short cycling), which can damage equipment like boilers, relays, and valves.')}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>{t('globalSettings.hysteresis.howItWorks', 'How it works:')}</strong> {t('globalSettings.hysteresis.example', 'If your target is 19.2°C and hysteresis is 0.5°C, heating starts at 18.7°C and stops at 19.2°C.')}
              </Typography>
              <Typography variant="body2">
                <strong>{t('globalSettings.hysteresis.recommendations', 'Recommendations:')}</strong>
              </Typography>
              <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px' }}>
                <li>{t('globalSettings.hysteresis.rec1', '0.1°C - Minimal delay, more frequent cycling (use only if needed)')}</li>
                <li>{t('globalSettings.hysteresis.rec2', '0.5°C - Balanced (default, recommended for most systems)')}</li>
                <li>{t('globalSettings.hysteresis.rec3', '1.0°C - Energy efficient, less wear on equipment')}</li>
              </ul>
              <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                💡 {t('globalSettings.hysteresis.tip', 'Tip: For immediate heating, use Boost Mode instead of reducing hysteresis.')}
              </Typography>
            </Alert>

            <Box>
              <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                {t('globalSettings.hysteresis.current', 'Current')}: {hysteresis.toFixed(1)}°C
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('globalSettings.hysteresis.heatingStarts', 'Heating starts when temperature drops')} {hysteresis.toFixed(1)}°C {t('globalSettings.hysteresis.belowTarget', 'below target')}
              </Typography>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
                <Slider
                  value={hysteresis}
                  onChange={handleHysteresisChange}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  marks={[
                    { value: 0.1, label: '0.1°C' },
                    { value: 0.5, label: '0.5°C' },
                    { value: 1.0, label: '1.0°C' },
                    { value: 2.0, label: '2.0°C' },
                  ]}
                  valueLabelDisplay="on"
                  valueLabelFormat={(v) => `${v.toFixed(1)}°C`}
                  disabled={saving}
                  sx={{ maxWidth: 600 }}
                />
              </Box>
            </Box>
          </Paper>

          {/* UI Settings */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('globalSettings.ui.title', 'User Interface')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {t('globalSettings.ui.description', 'Customize the user interface to your preferences.')}
            </Typography>

            <Stack spacing={2}>
              <Box sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 2,
                border: 1,
                borderColor: 'divider',
                borderRadius: 1
              }}>
                <Box>
                  <Typography variant="subtitle1">
                    {t('globalSettings.ui.hideDevicesPanel', 'Hide Available Devices Panel')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('globalSettings.ui.hideDevicesPanelDescription', 'Hide the sidebar with available devices when you\'re done setting up zones.')}
                  </Typography>
                </Box>
                <Switch
                  checked={hideDevicesPanel}
                  onChange={(e) => handleToggleHideDevicesPanel(e.target.checked)}
                  color="primary"
                />
              </Box>
            </Stack>
          </Paper>
          {/* Advanced Control Accordion */}
          <Accordion sx={{ mt: 3 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">{t('globalSettings.advanced.title', 'Advanced Boiler & Control')}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('globalSettings.advanced.description', 'Advanced features for optimizing setpoints, boiler cycling and energy efficiency. These are disabled by default. Enable to use advanced control algorithms (heating curves, PWM for on/off boilers, PID auto-gains, and calibration routines).')}
              </Typography>
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography>{t('globalSettings.advanced.enableAll', 'Enable advanced control')}</Typography>
                  <Switch checked={advancedControlEnabled} onChange={(e) => handleToggleAdvancedControl('advanced_control_enabled', e.target.checked)} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography>{t('globalSettings.advanced.heatingCurve', 'Heating curve')}</Typography>
                  <Switch checked={heatingCurveEnabled} onChange={(e) => handleToggleAdvancedControl('heating_curve_enabled', e.target.checked)} disabled={!advancedControlEnabled} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography>{t('globalSettings.advanced.pwm', 'PWM for on/off boilers')}</Typography>
                  <Switch checked={pwmEnabled} onChange={(e) => handleToggleAdvancedControl('pwm_enabled', e.target.checked)} disabled={!advancedControlEnabled} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography>{t('globalSettings.advanced.pid', 'PID Automatic Gains')}</Typography>
                  <Switch checked={pidEnabled} onChange={(e) => handleToggleAdvancedControl('pid_enabled', e.target.checked)} disabled={!advancedControlEnabled} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography>{t('globalSettings.advanced.overshoot', 'Overshoot Protection (OPV) calibration')}</Typography>
                  <Switch checked={overshootProtectionEnabled} onChange={(e) => handleToggleAdvancedControl('overshoot_protection_enabled', e.target.checked)} disabled={!advancedControlEnabled} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography>{t('globalSettings.advanced.defaultCoefficient', 'Default heating curve coefficient')}</Typography>
                  <input type='number' value={defaultCoefficient as any} onChange={(e) => handleToggleAdvancedControl('default_heating_curve_coefficient', Number(e.target.value))} step={0.1} disabled={!advancedControlEnabled} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                  <Button variant='contained' onClick={handleRunCalibration} disabled={!advancedControlEnabled || calibrating}>
                    {calibrating ? <CircularProgress size={20} /> : t('globalSettings.advanced.runCalibration', 'Run OPV calibration')}
                  </Button>
                  <Button variant='outlined' onClick={handleResetAdvancedControl} disabled={saving}>
                    {t('globalSettings.advanced.resetDefaults', 'Reset to defaults')}
                  </Button>
                  {calibrationResult !== null && (
                    <Typography variant='body2' sx={{ ml: 2 }}>
                      {t('globalSettings.advanced.calibrationResult', 'OPV: {{value}} °C', { value: calibrationResult })}
                    </Typography>
                  )}
                </Box>
              </Stack>
            </AccordionDetails>
          </Accordion>
        </TabPanel>

        {/* Import/Export Tab */}
        <TabPanel value={activeTab} index={5}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('importExport.title', 'Import/Export Configuration')}
            </Typography>
            <ImportExport />
          </Paper>
        </TabPanel>

        {/* OpenTherm Tab */}
        <TabPanel value={activeTab} index={6}>
          <Accordion defaultExpanded={false}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">
                {t('globalSettings.opentherm.title', 'OpenTherm Gateway Configuration')}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ mb: 3, p: 2, bgcolor: 'info.main', color: 'info.contrastText', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  ⚠️ {t('globalSettings.opentherm.importantNote', 'Important: Use Numeric ID Only')}
                </Typography>
                <Typography variant="body2">
                  {t('globalSettings.opentherm.description', 'Enter the numeric integration ID (e.g., 128937219831729813), NOT the entity ID (e.g., climate.opentherm_thermostaat).')}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {t('globalSettings.opentherm.findId', 'Find this ID in: Settings → Devices & Services → OpenTherm Gateway → Click "Configure" → Look for "ID" field (numeric value).')}
                </Typography>
              </Box>

              <Stack spacing={3}>
                {openthermGateways.length === 0 && (
                  <Alert severity="warning">
                    {t(
                      'globalSettings.opentherm.noGateways',
                      'No OpenTherm gateways found. Please add the OpenTherm Gateway integration in Home Assistant and configure its gateway ID.'
                    )}{' '}
                    <a href="/config/integrations" target="_blank" rel="noreferrer">
                      {t('globalSettings.openIntegrations', 'Open Integrations')}
                    </a>
                  </Alert>
                )}
                <FormControl fullWidth>
                  <InputLabel id="opentherm-gateway-select-label">{t('globalSettings.opentherm.gatewayId', 'Gateway Integration ID (ID or slug)')}</InputLabel>
                  <Select
                    labelId="opentherm-gateway-select-label"
                    value={openthermGatewayId}
                    label={t('globalSettings.opentherm.gatewayId', 'Gateway Integration ID (ID or slug)')}
                    onChange={(e) => setOpenthermGatewayId(e.target.value as string)}
                  >
                    <MenuItem value="">None (Disabled)</MenuItem>
                    {openthermGateways.map((g) => (
                      <MenuItem key={g.gateway_id} value={g.gateway_id}>
                        {g.title}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Removed manual enable toggle - control is automatic when a gateway id is configured */}

                <Button
                  variant="contained"
                  onClick={handleSaveOpenthermConfig}
                  // Disable when saving or there are no available gateways at all
                  disabled={openthermSaving || openthermGateways.length === 0}
                >
                  {openthermSaving ? (
                    <CircularProgress size={24} />
                  ) : (
                    t('globalSettings.opentherm.save', 'Save Configuration')
                  )}
                </Button>
              </Stack>
            </AccordionDetails>
          </Accordion>

          {/* Advanced Metrics Dashboard Link */}
          <Box sx={{ mt: 2, mb: 2 }}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate('/opentherm/metrics')}
              startIcon={<AssessmentIcon />}
            >
              {t('globalSettings.opentherm.advancedMetrics', 'View Advanced Metrics & Performance Dashboard')}
            </Button>
          </Box>

          <OpenThermLogger />
        </TabPanel>
      </Box>

      {/* Sensor Dialog */}
      <SensorConfigDialog
        open={sensorDialogOpen}
        onClose={() => setSensorDialogOpen(false)}
        onAdd={handleAddPresenceSensor}
        sensorType="presence"
      />

      {/* Safety Sensor Dialog */}
      <SafetySensorConfigDialog
        open={safetySensorDialogOpen}
        onClose={() => setSafetySensorDialogOpen(false)}
        onAdd={handleAddSafetySensor}
        configuredSensors={safetySensor?.sensors?.map(s => s.sensor_id) || []}
      />

      {/* Hysteresis Help Modal */}
      <HysteresisHelpModal
        open={hysteresisHelpOpen}
        onClose={() => setHysteresisHelpOpen(false)}
      />
    </Box>
  )
}
