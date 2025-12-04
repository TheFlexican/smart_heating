import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import TuneIcon from '@mui/icons-material/Tune'
import { Zone } from '../types'

interface DeviceOverviewProps {
  areas: Zone[]
}

const DeviceOverview = ({ areas }: DeviceOverviewProps) => {
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

  const getDeviceStatus = (device: any) => {
    if (device.type === 'thermostat') {
      if (device.hvac_action) {
        return device.hvac_action
      }
      return device.state || 'unknown'
    } else if (device.type === 'temperature_sensor') {
      if (device.temperature !== undefined && device.temperature !== null) {
        return `${device.temperature.toFixed(1)}°C`
      }
      return device.state || 'unknown'
    } else if (device.type === 'valve') {
      if (device.position !== undefined) {
        return `${device.position}%`
      }
      return device.state || 'unknown'
    } else {
      return device.state || 'unknown'
    }
  }

  const getDeviceDetails = (device: any) => {
    const parts = []
    
    if (device.type === 'thermostat') {
      if (device.current_temperature !== undefined && device.current_temperature !== null) {
        parts.push(`Current: ${device.current_temperature.toFixed(1)}°C`)
      }
      if (device.target_temperature !== undefined && device.target_temperature !== null) {
        parts.push(`Target: ${device.target_temperature.toFixed(1)}°C`)
      }
    }
    
    return parts.join(' | ') || '-'
  }

  const allDevices = areas.flatMap(area => 
    area.devices.map(device => ({
      ...device,
      areaName: area.name,
      areaId: area.id
    }))
  )

  if (allDevices.length === 0) {
    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Device Overview
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No devices found. Add devices to areas to see their status here.
        </Typography>
      </Paper>
    )
  }

  return (
    <Paper sx={{ mb: 3 }}>
      <Box p={2}>
        <Typography variant="h6" gutterBottom>
          Device Overview
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Real-time status of all devices across all areas
        </Typography>
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Device</TableCell>
              <TableCell>Area</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {allDevices.map((device) => (
              <TableRow key={`${device.areaId}-${device.id}`} hover>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getDeviceStatusIcon(device)}
                    <Typography variant="body2">
                      {device.name || device.id}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {device.areaName}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={device.type.replace(/_/g, ' ')} 
                    size="small" 
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={getDeviceStatus(device)}
                    size="small"
                    color={
                      device.type === 'thermostat' && device.hvac_action === 'heating' ? 'error' :
                      device.state === 'on' ? 'success' :
                      'default'
                    }
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="text.secondary">
                    {getDeviceDetails(device)}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )
}

export default DeviceOverview
