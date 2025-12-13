import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  CircularProgress,
  TextField,
  FormControlLabel,
  Switch,
} from '@mui/material'
// import { Droppable, Draggable } from 'react-beautiful-dnd' // TODO: Migrate to @dnd-kit
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import RouterIcon from '@mui/icons-material/Router'
import WaterIcon from '@mui/icons-material/Water'
import RefreshIcon from '@mui/icons-material/Refresh'
import { Device } from '../types'
import { refreshDevices } from '../api'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface DevicePanelProps {
  devices: Device[]
  onUpdate: () => void
}

const DevicePanel = ({ devices, onUpdate }: DevicePanelProps) => {
  const { t } = useTranslation()
  const [refreshing, setRefreshing] = useState(false)
  const [deviceSearch, setDeviceSearch] = useState('')
  const [showOnlyHeating, setShowOnlyHeating] = useState(true)

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refreshDevices()
      // Wait a moment for backend to update
      setTimeout(() => {
        onUpdate()
        setRefreshing(false)
      }, 500)
    } catch (error) {
      console.error('Failed to refresh devices:', error)
      setRefreshing(false)
    }
  }

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'thermostat':
        return <ThermostatIcon />
      case 'temperature_sensor':
        return <SensorsIcon />
      case 'opentherm_gateway':
        return <RouterIcon />
      case 'valve':
        return <WaterIcon />
      default:
        return <SensorsIcon />
    }
  }

  const getDeviceTypeLabel = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  // Filter devices based on search and type filter
  const filteredDevices = devices.filter(device => {
    // Type filter
    const typeMatch = !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')

    // Search filter
    if (!deviceSearch) return typeMatch

    const searchLower = deviceSearch.toLowerCase()
    const nameMatch = (device.name || device.id || '').toLowerCase().includes(searchLower)
    const entityMatch = (device.entity_id || device.id || '').toLowerCase().includes(searchLower)
    const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)

    return typeMatch && (nameMatch || entityMatch || areaMatch)
  })

  return (
    <Paper
      sx={{
        width: 320,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderLeft: 1,
        borderColor: 'divider',
        borderRadius: 0,
        bgcolor: 'background.paper',
      }}
      elevation={0}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h6" color="text.primary">
            {t('devices.availableCount', { count: filteredDevices.length })}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('devices.dragToAreas')}
          </Typography>
        </Box>
        <Tooltip title={t('devices.refreshTooltip')}>
          <IconButton
            onClick={handleRefresh}
            disabled={refreshing}
            size="small"
            sx={{ color: 'primary.main' }}
          >
            {refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
          </IconButton>
        </Tooltip>
      </Box>

      <Divider />

      {/* Filter Toggle */}
      <Box sx={{ px: 2, py: 1 }}>
        <FormControlLabel
          control={
            <Switch
              checked={showOnlyHeating}
              onChange={(e) => setShowOnlyHeating(e.target.checked)}
              size="small"
              color="primary"
            />
          }
          label={
            <Typography variant="caption" color="text.secondary">
              {t('devices.climateOnly')}
            </Typography>
          }
        />
      </Box>

      {/* Search Bar */}
      <Box sx={{ px: 2, pb: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={t('devices.searchPlaceholder')}
          value={deviceSearch}
          onChange={(e) => setDeviceSearch(e.target.value)}
        />
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {filteredDevices.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {deviceSearch
                ? t('devices.noMatch', { search: deviceSearch })
                : showOnlyHeating
                  ? t('devices.noClimateDevices')
                  : t('devices.noDevicesFound')}
            </Typography>
            {!deviceSearch && !showOnlyHeating && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {t('devices.configureInHA')}
              </Typography>
            )}
          </Box>
        ) : (
          <List>
            {filteredDevices.map((device) => (
              <ListItem
                key={device.id}
                sx={{
                  borderRadius: 1,
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.05)',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'text.secondary' }}>
                  {getDeviceIcon(device.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={device.name || device.id}
                          primaryTypographyProps={{ color: 'text.primary' }}
                          secondary={
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mt: 0.5 }}>
                              <Chip
                                label={getDeviceTypeLabel(device.type)}
                                size="small"
                                variant="outlined"
                                sx={{
                                  borderColor: 'divider',
                                  color: 'text.secondary',
                                  width: 'fit-content'
                                }}
                              />
                              {device.ha_area_name && (
                                <Typography variant="caption" color="text.secondary">
                                  📍 {device.ha_area_name}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Paper>
  )
}

export default DevicePanel
