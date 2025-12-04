import { useState } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  IconButton,
  Box,
  Chip,
  Slider,
  Switch,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import DeleteIcon from '@mui/icons-material/Delete'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import { Zone } from '../types'
import { setZoneTemperature, enableZone, disableZone, deleteZone } from '../api'

interface AreaCardProps {
  zone: Area
  onUpdate: () => void
}

const ZoneCard = ({ zone, onUpdate }: AreaCardProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [temperature, setTemperature] = useState(zone.target_temperature)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleToggle = async () => {
    try {
      if (zone.enabled) {
        await disableZone(zone.id)
      } else {
        await enableZone(zone.id)
      }
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle zone:', error)
    }
  }

  const handleTemperatureChange = async (_event: Event, value: number | number[]) => {
    const newTemp = value as number
    setTemperature(newTemp)
  }

  const handleTemperatureCommit = async (_event: Event | React.SyntheticEvent, value: number | number[]) => {
    try {
      await setZoneTemperature(zone.id, value as number)
      onUpdate()
    } catch (error) {
      console.error('Failed to set temperature:', error)
    }
  }

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete zone "${zone.name}"?`)) {
      try {
        await deleteZone(zone.id)
        onUpdate()
      } catch (error) {
        console.error('Failed to delete zone:', error)
      }
    }
    handleMenuClose()
  }

  const getStateColor = () => {
    switch (zone.state) {
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
    switch (zone.state) {
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

  return (
    <Card elevation={2}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {zone.name}
            </Typography>
            <Chip
              icon={getStateIcon()}
              label={zone.state.toUpperCase()}
              color={getStateColor()}
              size="small"
            />
          </Box>
          <Box>
            <Switch
              checked={zone.enabled}
              onChange={handleToggle}
              color="primary"
            />
            <IconButton size="small" onClick={handleMenuOpen}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        <Box my={3}>
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
            disabled={!zone.enabled}
          />
        </Box>

        {zone.current_temperature !== undefined && (
          <Box display="flex" justifyContent="space-between" mb={2}>
            <Typography variant="body2" color="text.secondary">
              Current Temperature
            </Typography>
            <Typography variant="body1">
              {zone.current_temperature}°C
            </Typography>
          </Box>
        )}

        <Box display="flex" alignItems="center" gap={1}>
          <SensorsIcon fontSize="small" color="action" />
          <Typography variant="body2" color="text.secondary">
            {zone.devices.length} device(s)
          </Typography>
        </Box>
      </CardContent>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete Zone</ListItemText>
        </MenuItem>
      </Menu>
    </Card>
  )
}

export default ZoneCard
