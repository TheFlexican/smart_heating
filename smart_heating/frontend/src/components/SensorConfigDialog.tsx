import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material'
import { HassEntity, WindowSensorConfig, PresenceSensorConfig } from '../types'
import { getBinarySensorEntities } from '../api'

interface SensorConfigDialogProps {
  open: boolean
  onClose: () => void
  onAdd: (config: WindowSensorConfig | PresenceSensorConfig) => Promise<void>
  sensorType: 'window' | 'presence'
}

const SensorConfigDialog = ({ open, onClose, onAdd, sensorType }: SensorConfigDialogProps) => {
  const [entities, setEntities] = useState<HassEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEntity, setSelectedEntity] = useState('')
  
  // Window sensor states
  const [windowAction, setWindowAction] = useState<'turn_off' | 'reduce_temperature' | 'none'>('reduce_temperature')
  const [windowTempDrop, setWindowTempDrop] = useState(5)
  
  // Presence sensor states
  const [awayAction, setAwayAction] = useState<'turn_off' | 'reduce_temperature' | 'set_eco' | 'none'>('reduce_temperature')
  const [homeAction, setHomeAction] = useState<'increase_temperature' | 'set_comfort' | 'none'>('increase_temperature')
  const [awayTempDrop, setAwayTempDrop] = useState(3)
  const [homeTempBoost, setHomeTempBoost] = useState(2)

  useEffect(() => {
    if (open) {
      loadEntities()
    }
  }, [open])

  const loadEntities = async () => {
    setLoading(true)
    try {
      // API now returns binary sensors, person, and device_tracker entities
      const data = await getBinarySensorEntities()
      setEntities(data)
    } catch (error) {
      console.error('Failed to load entities:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!selectedEntity) {
      return
    }

    try {
      if (sensorType === 'window') {
        const config: WindowSensorConfig = {
          entity_id: selectedEntity,
          action_when_open: windowAction,
        }
        if (windowAction === 'reduce_temperature') {
          config.temp_drop = windowTempDrop
        }
        await onAdd(config)
      } else {
        const config: PresenceSensorConfig = {
          entity_id: selectedEntity,
          action_when_away: awayAction,
          action_when_home: homeAction,
        }
        if (awayAction === 'reduce_temperature') {
          config.temp_drop_when_away = awayTempDrop
        }
        if (homeAction === 'increase_temperature') {
          config.temp_boost_when_home = homeTempBoost
        }
        await onAdd(config)
      }
      
      handleClose()
    } catch (error) {
      console.error('Failed to add sensor:', error)
    }
  }

  const handleClose = () => {
    setSelectedEntity('')
    setWindowAction('reduce_temperature')
    setWindowTempDrop(5)
    setAwayAction('reduce_temperature')
    setHomeAction('increase_temperature')
    setAwayTempDrop(3)
    setHomeTempBoost(2)
    onClose()
  }

  // Filter entities by device class for better UX
  const filteredEntities = entities.filter(e => {
    if (sensorType === 'window') {
      return e.attributes.device_class === 'window' || 
             e.attributes.device_class === 'door' || 
             e.attributes.device_class === 'opening'
    } else {
      // For presence sensors: include motion, occupancy, presence sensors
      // Also include person and device_tracker entities (marked with device_class: presence by backend)
      return e.attributes.device_class === 'motion' || 
             e.attributes.device_class === 'occupancy' || 
             e.attributes.device_class === 'presence'
    }
  })

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {sensorType === 'window' ? 'Add Window Sensor' : 'Add Presence Sensor'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <FormControl fullWidth>
                <InputLabel>Entity</InputLabel>
                <Select
                  value={selectedEntity}
                  label="Entity"
                  onChange={(e) => setSelectedEntity(e.target.value)}
                >
                  {filteredEntities.length > 0 ? (
                    filteredEntities.map((entity) => (
                      <MenuItem key={entity.entity_id} value={entity.entity_id}>
                        {entity.attributes.friendly_name || entity.entity_id}
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>
                      No {sensorType === 'window' ? 'window/door' : 'motion/presence'} sensors found
                    </MenuItem>
                  )}
                </Select>
              </FormControl>

              {filteredEntities.length === 0 && (
                <Alert severity="info">
                  No suitable sensors found. You can also manually enter an entity ID:
                  <TextField
                    size="small"
                    fullWidth
                    placeholder={sensorType === 'window' 
                      ? 'binary_sensor.window_living_room' 
                      : 'binary_sensor.motion_living_room or person.john or device_tracker.iphone'}
                    value={selectedEntity}
                    onChange={(e) => setSelectedEntity(e.target.value)}
                    sx={{ mt: 1 }}
                  />
                </Alert>
              )}

              {sensorType === 'window' ? (
                // Window Sensor Configuration
                <>
                  <FormControl fullWidth>
                    <InputLabel>Action When Open</InputLabel>
                    <Select
                      value={windowAction}
                      label="Action When Open"
                      onChange={(e) => setWindowAction(e.target.value as any)}
                    >
                      <MenuItem value="reduce_temperature">Reduce Temperature</MenuItem>
                      <MenuItem value="turn_off">Turn Off Heating</MenuItem>
                      <MenuItem value="none">No Action</MenuItem>
                    </Select>
                  </FormControl>

                  {windowAction === 'reduce_temperature' && (
                    <TextField
                      label="Temperature Drop (°C)"
                      type="number"
                      value={windowTempDrop}
                      onChange={(e) => setWindowTempDrop(Number(e.target.value))}
                      inputProps={{ min: 1, max: 10, step: 0.5 }}
                      helperText="How much to reduce temperature when window is open"
                      fullWidth
                    />
                  )}
                </>
              ) : (
                // Presence Sensor Configuration
                <>
                  <Typography variant="subtitle2" color="text.secondary">
                    When Away (No Presence)
                  </Typography>
                  <FormControl fullWidth>
                    <InputLabel>Action When Away</InputLabel>
                    <Select
                      value={awayAction}
                      label="Action When Away"
                      onChange={(e) => setAwayAction(e.target.value as any)}
                    >
                      <MenuItem value="reduce_temperature">Reduce Temperature</MenuItem>
                      <MenuItem value="set_eco">Set to Eco Mode</MenuItem>
                      <MenuItem value="turn_off">Turn Off Heating</MenuItem>
                      <MenuItem value="none">No Action</MenuItem>
                    </Select>
                  </FormControl>

                  {awayAction === 'reduce_temperature' && (
                    <TextField
                      label="Temperature Drop When Away (°C)"
                      type="number"
                      value={awayTempDrop}
                      onChange={(e) => setAwayTempDrop(Number(e.target.value))}
                      inputProps={{ min: 1, max: 10, step: 0.5 }}
                      helperText="How much to reduce temperature when away"
                      fullWidth
                    />
                  )}

                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>
                    When Home (Presence Detected)
                  </Typography>
                  <FormControl fullWidth>
                    <InputLabel>Action When Home</InputLabel>
                    <Select
                      value={homeAction}
                      label="Action When Home"
                      onChange={(e) => setHomeAction(e.target.value as any)}
                    >
                      <MenuItem value="increase_temperature">Increase Temperature</MenuItem>
                      <MenuItem value="set_comfort">Set to Comfort Mode</MenuItem>
                      <MenuItem value="none">No Action</MenuItem>
                    </Select>
                  </FormControl>

                  {homeAction === 'increase_temperature' && (
                    <TextField
                      label="Temperature Boost When Home (°C)"
                      type="number"
                      value={homeTempBoost}
                      onChange={(e) => setHomeTempBoost(Number(e.target.value))}
                      inputProps={{ min: 0.5, max: 5, step: 0.5 }}
                      helperText="How much to increase temperature when home"
                      fullWidth
                    />
                  )}
                </>
              )}
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleAdd} variant="contained" disabled={!selectedEntity}>
          Add Sensor
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default SensorConfigDialog
