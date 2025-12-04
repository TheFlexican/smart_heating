import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider
} from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import RouterIcon from '@mui/icons-material/Router'
import WaterIcon from '@mui/icons-material/Water'
import { Device } from '../types'

interface DevicePanelProps {
  devices: Device[]
  onUpdate: () => void
}

const DevicePanel = ({ devices, onUpdate }: DevicePanelProps) => {
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

  return (
    <Paper
      sx={{
        width: 320,
        display: 'flex',
        flexDirection: 'column',
        borderLeft: 1,
        borderColor: 'divider',
        borderRadius: 0,
      }}
      elevation={0}
    >
      <Box sx={{ p: 2, bgcolor: 'background.default' }}>
        <Typography variant="h6">
          Available Devices
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Drag devices to zones
        </Typography>
      </Box>

      <Divider />

      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {devices.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No Zigbee2MQTT devices found
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Make sure Zigbee2MQTT is running and devices are paired
            </Typography>
          </Box>
        ) : (
          <List>
            {devices.map((device) => (
              <ListItem
                key={device.id}
                sx={{
                  cursor: 'grab',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                }}
                draggable
              >
                <ListItemIcon>
                  {getDeviceIcon(device.type)}
                </ListItemIcon>
                <ListItemText
                  primary={device.name || device.id}
                  secondary={
                    <Chip
                      label={getDeviceTypeLabel(device.type)}
                      size="small"
                      variant="outlined"
                      sx={{ mt: 0.5 }}
                    />
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
