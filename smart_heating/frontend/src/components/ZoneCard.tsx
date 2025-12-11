import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Card,
  CardContent,
  Typography,
  IconButton,
  Box,
  Chip,
  Slider,
  Menu,
  ListItemText,
  List,
  ListItem,
  ListItemIcon,
  MenuItem,
  FormControlLabel,
  Switch,
  Tooltip,
  alpha
} from '@mui/material'
import { Droppable, Draggable } from 'react-beautiful-dnd'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import TuneIcon from '@mui/icons-material/Tune'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import VisibilityIcon from '@mui/icons-material/Visibility'
import PersonIcon from '@mui/icons-material/Person'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'
import { Zone } from '../types'
import { setZoneTemperature, removeDeviceFromZone, hideZone, unhideZone, getEntityState, setManualOverride, setBoostMode, cancelBoost } from '../api'

interface ZoneCardProps {
  area: Zone
  onUpdate: () => void
  index: number
}

const ZoneCard = ({ area, onUpdate, index }: ZoneCardProps) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  // Get displayed temperature: use effective temperature when in preset mode, otherwise use target
  const getDisplayTemperature = () => {
    // When using preset mode (not manual override), show effective temperature
    if (!area.manual_override && area.preset_mode && area.preset_mode !== 'none' && area.effective_target_temperature != null) {
      return area.effective_target_temperature
    }
    // Otherwise show the base target temperature
    return area.target_temperature
  }

  const [temperature, setTemperature] = useState(getDisplayTemperature())
  const [presenceState, setPresenceState] = useState<string | null>(null)

  // Sync local temperature state when area or devices change
  useEffect(() => {
    const displayTemp = getDisplayTemperature()
    setTemperature(displayTemp)
  }, [area.target_temperature, area.effective_target_temperature, area.manual_override, area.preset_mode, area.name])

  useEffect(() => {
    const loadPresenceState = async () => {
      if (area.presence_sensors && area.presence_sensors.length > 0) {
        try {
          const firstSensor = area.presence_sensors[0]
          const state = await getEntityState(firstSensor.entity_id)
          setPresenceState(state.state)
        } catch (error) {
          console.error('Failed to load presence state:', error)
        }
      }
    }
    loadPresenceState()
  }, [area.presence_sensors])

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleCardClick = () => {
    navigate(`/area/${area.id}`)
  }

  const handleTemperatureChange = async (event: Event, value: number | number[]) => {
    event.stopPropagation()
    const newTemp = value as number
    setTemperature(newTemp)
  }

  const handleTemperatureCommit = async (event: Event | React.SyntheticEvent, value: number | number[]) => {
    event.stopPropagation()
    try {
      await setZoneTemperature(area.id, value as number)
      onUpdate()
    } catch (error) {
      console.error('Failed to set temperature:', error)
    }
  }

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      await removeDeviceFromZone(area.id, deviceId)
      onUpdate()
    } catch (error) {
      console.error('Failed to remove device:', error)
    }
  }

  const handleToggleHidden = async (event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      if (area.hidden) {
        await unhideZone(area.id)
      } else {
        await hideZone(area.id)
      }
      handleMenuClose()
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle hidden:', error)
    }
  }

  const handleSliderClick = (event: React.MouseEvent) => {
    event.stopPropagation()
  }

  const handleBoostToggle = async (event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      if (area.boost_mode_active) {
        await cancelBoost(area.id)
      } else {
        // Use area's boost settings or defaults
        const boostTemp = area.boost_temp || 25
        const boostDuration = area.boost_duration || 60
        await setBoostMode(area.id, boostDuration, boostTemp)
      }
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle boost mode:', error)
    }
  }

  const getStateColor = () => {
    if (area.manual_override) {
      return 'warning'
    }
    switch (area.state) {
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

  const getStateIcon = () => {
    if (area.manual_override) {
      return <TuneIcon />
    }
    switch (area.state) {
      case 'heating':
        return <LocalFireDepartmentIcon />
      case 'idle':
        return <ThermostatIcon />
      case 'off':
        return <AcUnitIcon />
      default:
        return <ThermostatIcon />
    }
  }

  const formatTemperature = (temp: number | undefined | null): string | null => {
    if (temp === undefined || temp === null) return null
    return `${temp.toFixed(1)}°C`
  }

  const isValidState = (state: string | undefined): boolean => {
    return state !== undefined && state !== 'unavailable' && state !== 'unknown'
  }

  const getThermostatStatus = (device: any): string[] => {
    const parts = []

    // Add hvac_action if available (heating, cooling, idle, etc.)
    if (device.hvac_action && device.hvac_action !== 'idle' && device.hvac_action !== 'off') {
      const key = `area.${device.hvac_action}`
      const translatedAction = t(key, { defaultValue: device.hvac_action })
      parts.push(`[${translatedAction}]`)
    }

    const currentTemp = formatTemperature(device.current_temperature)
    if (currentTemp) {
      parts.push(currentTemp)
    }

    // Use area's target temperature instead of device's stale target
    const areaTarget = area.target_temperature
    if (areaTarget !== undefined && areaTarget !== null &&
        device.current_temperature !== undefined && device.current_temperature !== null &&
        areaTarget > device.current_temperature) {
      const targetTemp = formatTemperature(areaTarget)
      if (targetTemp) parts.push(`→ ${targetTemp}`)
    }

    if (parts.length === 0 && device.state) {
      // Translate common states
      const key = `area.${device.state}`
      const translatedState = t(key, { defaultValue: device.state })
      parts.push(translatedState)
    }

    return parts
  }

  const getTemperatureSensorStatus = (device: any): string[] => {
    const parts = []

    const temp = formatTemperature(device.temperature)
    if (temp) {
      parts.push(temp)
    } else if (isValidState(device.state)) {
      parts.push(`${device.state}°C`)
    }

    return parts
  }

  const getValveStatus = (device: any): string[] => {
    const parts = []

    if (device.position !== undefined && device.position !== null) {
      parts.push(`${device.position}%`)
    } else if (isValidState(device.state)) {
      parts.push(`${device.state}%`)
    }

    return parts
  }

  const getGenericDeviceStatus = (device: any): string[] => {
    const parts = []

    if (isValidState(device.state)) {
      // Translate common states (on, off, etc.)
      const key = `area.${device.state}`
      const translatedState = t(key, { defaultValue: device.state })
      parts.push(translatedState)
    }

    return parts
  }

  const getDeviceStatusText = (device: any): string => {
    let parts: string[] = []

    if (device.type === 'thermostat') {
      parts = getThermostatStatus(device)
    } else if (device.type === 'temperature_sensor') {
      parts = getTemperatureSensorStatus(device)
    } else if (device.type === 'valve') {
      parts = getValveStatus(device)
    } else {
      parts = getGenericDeviceStatus(device)
    }

    return parts.length > 0 ? parts.join(' · ') : 'unavailable'
  }

  return (
    <Draggable draggableId={`area-card-${area.id}`} index={index}>
      {(dragProvided, dragSnapshot) => (
        <div
          ref={dragProvided.innerRef}
          {...dragProvided.draggableProps}
        >
          <Droppable droppableId={`area-${area.id}`}>
            {(provided, snapshot) => (
              <Card
                ref={provided.innerRef}
                {...provided.droppableProps}
                elevation={dragSnapshot.isDragging ? 8 : 2}
                onClick={handleCardClick}
                sx={{
                  bgcolor: snapshot.isDraggingOver
                    ? alpha('#03a9f4', 0.08)
                    : dragSnapshot.isDragging
                    ? alpha('#03a9f4', 0.12)
                    : 'background.paper',
                  border: snapshot.isDraggingOver ? '2px dashed #03a9f4' : 'none',
                  borderRadius: 3,
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  cursor: 'pointer',
                  transform: dragSnapshot.isDragging ? 'scale(1.02)' : 'scale(1)',
                  boxShadow: dragSnapshot.isDragging
                    ? '0 8px 24px rgba(0,0,0,0.4)'
                    : undefined,
                  '&:hover': {
                    bgcolor: snapshot.isDraggingOver ? alpha('#03a9f4', 0.08) : alpha('#ffffff', 0.05),
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  },
                }}
              >
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  {/* Drag Handle */}
                  <Box
                    {...dragProvided.dragHandleProps}
                    sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      cursor: 'grab',
                      color: 'text.secondary',
                      opacity: 0.3,
                      transition: 'opacity 0.2s',
                      '&:hover': {
                        opacity: 0.8,
                      },
                      '&:active': {
                        cursor: 'grabbing',
                      },
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <DragIndicatorIcon fontSize="small" />
                  </Box>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              {area.name}
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Chip
                icon={getStateIcon()}
                label={area.manual_override ? t('area.manual') : t(`area.${area.state}`, { defaultValue: area.state }).toUpperCase()}
                color={getStateColor()}
                size="small"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
              {area.presence_sensors && area.presence_sensors.length > 0 && presenceState && (
                <Chip
                  icon={<PersonIcon />}
                  label={t(`presets.${presenceState}`, { defaultValue: presenceState }).toUpperCase()}
                  color={presenceState === 'home' ? 'success' : 'default'}
                  size="small"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
                />
              )}
              {area.boost_mode_active && (
                <Chip
                  icon={<RocketLaunchIcon />}
                  label={t('presets.boost', { defaultValue: 'BOOST' }).toUpperCase()}
                  color="error"
                  size="small"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
                />
              )}
            </Box>
          </Box>
          <Box onClick={(e) => e.stopPropagation()} display="flex" gap={1}>
            <Tooltip title={area.boost_mode_active ? t('boost.quickBoostActive') : t('boost.quickBoostInactive')}>
              <IconButton
                size="small"
                onClick={handleBoostToggle}
                sx={{
                  p: { xs: 0.5, sm: 1 },
                  color: area.boost_mode_active ? 'error.main' : 'text.secondary',
                  bgcolor: area.boost_mode_active ? 'error.dark' : 'transparent',
                  '&:hover': {
                    bgcolor: area.boost_mode_active ? 'error.dark' : 'rgba(255, 255, 255, 0.08)',
                  }
                }}
              >
                <RocketLaunchIcon />
              </IconButton>
            </Tooltip>
            <IconButton size="small" onClick={handleMenuOpen} sx={{ p: { xs: 0.5, sm: 1 } }}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        <Box my={{ xs: 2, sm: 3 }} onClick={handleSliderClick}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
              {t('area.targetTemperature')}
              {area.preset_mode && area.preset_mode !== 'none' && (
                <Chip
                  label={t(`presets.${area.preset_mode}`).toUpperCase()}
                  size="small"
                  color="secondary"
                  sx={{ ml: 1, fontSize: { xs: '0.65rem', sm: '0.7rem' }, height: '20px' }}
                />
              )}
            </Typography>
            <Typography variant="h5" color="primary" sx={{ fontSize: { xs: '1.5rem', sm: '2rem' } }}>
              {temperature}°C
            </Typography>
          </Box>
          <Slider
            value={temperature}
            onChange={handleTemperatureChange}
            onChangeCommitted={handleTemperatureCommit}
            min={5}
            max={30}
            step={0.1}
            marks={[
              { value: 5, label: '5°' },
              { value: 30, label: '30°' }
            ]}
            valueLabelDisplay="auto"
            disabled={!area.enabled || area.devices.length === 0 || !area.manual_override}
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
          />
          {area.devices.length === 0 && (
            <Box display="flex" alignItems="center" gap={1} mt={1} sx={{ color: 'warning.main' }}>
              <InfoOutlinedIcon fontSize="small" />
              <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                {t('area.addDevicesPrompt')}
              </Typography>
            </Box>
          )}
        </Box>

        {area.current_temperature !== undefined && area.current_temperature !== null && (
          <Box display="flex" justifyContent="space-between" mb={2}>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
              {t('area.currentTemperature')}
            </Typography>
            <Typography variant="body1" sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
              {area.current_temperature.toFixed(1)}°C
            </Typography>
          </Box>
        )}

        {/* Manual Override Toggle */}
        <Box mb={2} onClick={(e) => e.stopPropagation()}>
          <FormControlLabel
            control={
              <Switch
                checked={!area.manual_override}
                onChange={async (e) => {
                  try {
                    // Toggle: if checked (not manual), user wants to use preset mode
                    await setManualOverride(area.id, !e.target.checked)
                    onUpdate()
                  } catch (error) {
                    console.error('Failed to toggle manual override:', error)
                  }
                }}
                size="small"
              />
            }
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <BookmarkIcon fontSize="small" />
                <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {area.manual_override ? t('area.usePresetMode') : t('area.usingPresetMode')}
                </Typography>
              </Box>
            }
          />
        </Box>

        <Box display="flex" alignItems="center" gap={1} mb={area.devices.length > 0 ? 2 : 0}>
          <SensorsIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
            {t('area.deviceCount', { count: area.devices.length })}
            {snapshot.isDraggingOver && ` - ${t('area.dropToAdd')}`}
          </Typography>
        </Box>

        {area.devices.length > 0 && (
          <List dense sx={{ mt: 1, bgcolor: 'rgba(255,255,255,0.02)', borderRadius: 1 }}>
            {area.devices.map((device) => (
              <ListItem
                key={device.id}
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveDevice(device.id)
                    }}
                    sx={{
                      color: 'text.secondary',
                      p: { xs: 0.5, sm: 1 }
                    }}
                  >
                    <RemoveCircleOutlineIcon fontSize="small" />
                  </IconButton>
                }
                sx={{
                  py: { xs: 0.5, sm: 1 },
                  pr: { xs: 5, sm: 6 }
                }}
              >
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      color="text.primary"
                      sx={{
                        fontSize: { xs: '0.8rem', sm: '0.875rem' },
                        wordBreak: 'break-word'
                      }}
                    >
                      {device.name || device.id}
                    </Typography>
                  }
                  secondary={getDeviceStatusText(device)}
                  slotProps={{
                    secondary: {
                      variant: 'caption',
                      color: 'text.secondary',
                      sx: { fontSize: { xs: '0.7rem', sm: '0.75rem' } }
                    }
                  }}
                />
              </ListItem>
            ))}
          </List>
        )}
        {provided.placeholder}
      </CardContent>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleToggleHidden}>
          <ListItemIcon>
            {area.hidden ? <VisibilityIcon /> : <VisibilityOffIcon />}
          </ListItemIcon>
          <ListItemText primary={area.hidden ? t('area.unhideArea') : t('area.hideArea')} />
        </MenuItem>
      </Menu>
    </Card>
          )}
        </Droppable>
      </div>
      )}
    </Draggable>
  )
}

export default ZoneCard
