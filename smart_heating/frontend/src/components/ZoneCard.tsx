import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  MenuItem
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
import { Zone } from '../types'
import { setZoneTemperature, removeDeviceFromZone, hideZone, unhideZone } from '../api'

interface ZoneCardProps {
  area: Zone
  onUpdate: () => void
}

const ZoneCard = ({ area, onUpdate }: ZoneCardProps) => {
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [temperature, setTemperature] = useState(area.target_temperature)

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

  const getDeviceStatusText = (device: any) => {
    const parts = []
    
    if (device.type === 'thermostat') {
      if (device.current_temperature !== undefined && device.current_temperature !== null) {
        parts.push(`${device.current_temperature.toFixed(1)}°C`)
      }
      if (device.target_temperature !== undefined && device.target_temperature !== null && 
          device.current_temperature !== undefined && device.current_temperature !== null &&
          device.target_temperature > device.current_temperature) {
        parts.push(`→ ${device.target_temperature.toFixed(1)}°C`)
      }
      if (parts.length === 0 && device.state) {
        parts.push(device.state)
      }
    } else if (device.type === 'temperature_sensor') {
      if (device.temperature !== undefined && device.temperature !== null) {
        parts.push(`${device.temperature.toFixed(1)}°C`)
      } else if (device.state && device.state !== 'unavailable' && device.state !== 'unknown') {
        parts.push(`${device.state}°C`)
      }
    } else if (device.type === 'valve') {
      if (device.position !== undefined && device.position !== null) {
        parts.push(`${device.position}%`)
      } else if (device.state && device.state !== 'unavailable' && device.state !== 'unknown') {
        parts.push(`${device.state}%`)
      }
    } else {
      if (device.state && device.state !== 'unavailable' && device.state !== 'unknown') {
        parts.push(device.state)
      }
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
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {area.name}
            </Typography>
            <Chip
              icon={getStateIcon()}
              label={area.state.toUpperCase()}
              color={getStateColor()}
              size="small"
            />
          </Box>
          <Box onClick={(e) => e.stopPropagation()}>
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        <Box my={3} onClick={handleSliderClick}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" color="text.secondary">
              Target Temperature
            </Typography>
            <Typography variant="h5" color="primary">
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
              { value: 30, label: '30°' }
            ]}
            valueLabelDisplay="auto"
            disabled={!area.enabled || area.devices.length === 0}
          />
          {area.devices.length === 0 && (
            <Box display="flex" alignItems="center" gap={1} mt={1} sx={{ color: 'warning.main' }}>
              <InfoOutlinedIcon fontSize="small" />
              <Typography variant="caption">
                Add devices to this area to control temperature
              </Typography>
            </Box>
          )}
        </Box>

        {area.current_temperature !== undefined && area.current_temperature !== null && (
          <Box display="flex" justifyContent="space-between" mb={2}>
            <Typography variant="body2" color="text.secondary">
              Current Temperature
            </Typography>
            <Typography variant="body1">
              {area.current_temperature.toFixed(1)}°C
            </Typography>
          </Box>
        )}

        <Box display="flex" alignItems="center" gap={1} mb={area.devices.length > 0 ? 2 : 0}>
          <SensorsIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary">
            {area.devices.length} device(s)
            {snapshot.isDraggingOver && ' - Drop here to add'}
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
                    sx={{ color: 'text.secondary' }}
                  >
                    <RemoveCircleOutlineIcon fontSize="small" />
                  </IconButton>
                }
                sx={{ py: 0.5 }}
              >
                <Box sx={{ mr: 1, display: 'flex', alignItems: 'center', minWidth: 24 }}>
                  {getDeviceStatusIcon(device)}
                </Box>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" color="text.primary">
                        {device.name || device.id}
                      </Typography>
                      {device.type === 'thermostat' && device.hvac_action && (
                        <Chip 
                          label={device.hvac_action} 
                          size="small" 
                          sx={{ 
                            height: 18, 
                            fontSize: '0.65rem',
                            bgcolor: device.hvac_action === 'heating' ? 'error.main' : 'info.main'
                          }} 
                        />
                      )}
                    </Box>
                  }
                  secondary={getDeviceStatusText(device)}
                  secondaryTypographyProps={{
                    variant: 'caption',
                    color: 'text.secondary'
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
          <ListItemText primary={area.hidden ? "Unhide Area" : "Hide Area"} />
        </MenuItem>
      </Menu>
    </Card>
      )}
    </Droppable>
  )
}

export default ZoneCard
