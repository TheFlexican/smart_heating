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
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import { useNavigate } from 'react-router-dom'
import { getGlobalPresets, setGlobalPresets, getGlobalPresence, setGlobalPresence, getHysteresis, setHysteresis } from '../api'
import { PresenceSensorConfig, WindowSensorConfig } from '../types'
import SensorConfigDialog from '../components/SensorConfigDialog'
import { VacationModeSettings } from '../components/VacationModeSettings'
import HysteresisHelpModal from '../components/HysteresisHelpModal'

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

export default function GlobalSettings() {
  const navigate = useNavigate()
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

  useEffect(() => {
    loadPresets()
    loadHysteresis()
    loadPresenceSensors()
  }, [])

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
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', pb: 4 }}>
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
        <Typography variant="h6">Global Preset Temperatures</Typography>
      </Paper>

      <Box sx={{ px: 2 }}>
        {/* Vacation Mode Section */}
        <VacationModeSettings />

        {saveSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Preset saved successfully
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Preset Temperatures
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            These are the default temperatures for each preset mode. Areas can choose to use these global settings or define their own custom temperatures.
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
            💡 Tip: To customize temperatures for a specific area, go to that area's settings and toggle off "Use global preset" for individual preset modes.
          </Typography>
        </Paper>

        {/* Hysteresis Settings */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="h6">
              Temperature Hysteresis
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
            Controls the temperature buffer to prevent rapid on/off cycling of your heating system.
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>What is hysteresis?</strong>
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              Hysteresis prevents your heating system from constantly turning on and off (short cycling), which can damage equipment like boilers, relays, and valves.
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>How it works:</strong> If your target is 19.2°C and hysteresis is 0.5°C, heating starts at 18.7°C and stops at 19.2°C.
            </Typography>
            <Typography variant="body2">
              <strong>Recommendations:</strong>
            </Typography>
            <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px' }}>
              <li>0.1°C - Minimal delay, more frequent cycling (use only if needed)</li>
              <li>0.5°C - Balanced (default, recommended for most systems)</li>
              <li>1.0°C - Energy efficient, less wear on equipment</li>
            </ul>
            <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
              💡 Tip: For immediate heating, use Boost Mode instead of reducing hysteresis.
            </Typography>
          </Alert>

          <Box>
            <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
              Current: {hysteresis.toFixed(1)}°C
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Heating starts when temperature drops {hysteresis.toFixed(1)}°C below target
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

        {/* Global Presence Sensors */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Global Presence Sensors
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Configure presence sensors that can be used across all areas. Areas can choose to use these global sensors or configure their own.
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
                    secondary="Switches heating to 'away' when nobody is home"
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Alert severity="info" sx={{ mb: 2 }}>
              No global presence sensors configured. Add sensors that will be available to all areas.
            </Alert>
          )}

          <Button
            variant="outlined"
            fullWidth
            onClick={() => setSensorDialogOpen(true)}
            sx={{ mt: 2 }}
          >
            Add Presence Sensor
          </Button>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
            💡 Tip: Areas can enable "Use global presence" in their settings to use these sensors instead of configuring their own.
          </Typography>
        </Paper>
      </Box>

      {/* Sensor Dialog */}
      <SensorConfigDialog
        open={sensorDialogOpen}
        onClose={() => setSensorDialogOpen(false)}
        onAdd={handleAddPresenceSensor}
        sensorType="presence"
      />

      {/* Hysteresis Help Modal */}
      <HysteresisHelpModal
        open={hysteresisHelpOpen}
        onClose={() => setHysteresisHelpOpen(false)}
      />
    </Box>
  )
}
