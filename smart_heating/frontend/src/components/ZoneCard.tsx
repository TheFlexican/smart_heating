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
  Switch
} from '@mui/material'
import { Droppable } from 'react-beautiful-dnd'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import TuneIcon from '@mui/icons-material/Tune'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import VisibilityIcon from '@mui/icons-material/Visibility'
import PersonIcon from '@mui/icons-material/Person'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import { Zone } from '../types'
import { setZoneTemperature, removeDeviceFromZone, hideZone, unhideZone, getEntityState, setManualOverride } from '../api'

interface ZoneCardProps {
  area: Zone
  onUpdate: () => void
}

const ZoneCard = ({ area, onUpdate }: ZoneCardProps) => {
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

  const getDeviceStatusIcon = (device: any) => {
    if (device.type === 'thermostat') {
      if (device.hvac_action === 'heating') {
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

  const formatTemperature = (temp: number | undefined | null): string | null => {
    if (temp === undefined || temp === null) return null
    return `${temp.toFixed(1)}°C`
  }

  const isValidState = (state: string | undefined): boolean => {
    return state !== undefined && state !== 'unavailable' && state !== 'unknown'
  }

  const getThermostatStatus = (device: any): string[] => {
    const parts = []
    
    const currentTemp = formatTemperature(device.current_temperature)
    if (currentTemp) {
      parts.push(currentTemp)
    }
    
    if (device.target_temperature !== undefined && device.target_temperature !== null && 
        device.current_temperature !== undefined && device.current_temperature !== null &&
        device.target_temperature > device.current_temperature) {
      parts.push(`→ ${device.target_temperature.toFixed(1)}°C`)
    }
    
    if (parts.length === 0 && device.state) {
      parts.push(device.state)
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
      parts.push(device.state)
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
    <Droppable droppableId={`area-${area.id}`}>
      {(provided, snapshot) => (
        <Card 
          ref={provided.innerRef}
          {...provided.droppableProps}
          elevation={2}
          onClick={handleCardClick}
          sx={{
            bgcolor: snapshot.isDraggingOver ? 'rgba(3, 169, 244, 0.05)' : 'background.paper',
            border: snapshot.isDraggingOver ? '2px dashed #03a9f4' : 'none',
            transition: 'all 0.2s ease',
            cursor: 'pointer',
            '&:hover': {
              bgcolor: snapshot.isDraggingOver ? 'rgba(3, 169, 244, 0.05)' : 'rgba(255, 255, 255, 0.05)',
            },
          }}
        >
      <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              {area.name}
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Chip
                icon={getStateIcon()}
                label={area.manual_override ? t('area.manual') : area.state.toUpperCase()}
                color={getStateColor()}
                size="small"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
              {area.presence_sensors && area.presence_sensors.length > 0 && presenceState && (
                <Chip
                  icon={<PersonIcon />}
                  label={presenceState.toUpperCase()}
                  color={presenceState === 'home' ? 'success' : 'default'}
                  size="small"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
                />
              )}
            </Box>
          </Box>
          <Box onClick={(e) => e.stopPropagation()}>
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
                  label={area.preset_mode.toUpperCase()} 
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
                <Box sx={{ mr: { xs: 0.5, sm: 1 }, display: 'flex', alignItems: 'center', minWidth: 24 }}>
                  {getDeviceStatusIcon(device)}
                </Box>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
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
                      {device.type === 'thermostat' && device.hvac_action && (
                        <Chip 
                          label={device.hvac_action} 
                          size="small" 
                          sx={{ 
                            height: { xs: 16, sm: 18 }, 
                            fontSize: { xs: '0.6rem', sm: '0.65rem' },
                            bgcolor: device.hvac_action === 'heating' ? 'error.main' : 'info.main'
                          }} 
                        />
                      )}
                    </Box>
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
  )
}

export default ZoneCard
