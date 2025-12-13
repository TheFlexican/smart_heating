import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Collapse,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import DeleteIcon from '@mui/icons-material/Delete'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import HomeIcon from '@mui/icons-material/Home'
import InfoIcon from '@mui/icons-material/Info'
import WhatshotIcon from '@mui/icons-material/Whatshot'
import SpeedIcon from '@mui/icons-material/Speed'
import OpacityIcon from '@mui/icons-material/Opacity'
import ErrorIcon from '@mui/icons-material/Error'
import WarningIcon from '@mui/icons-material/Warning'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import BuildIcon from '@mui/icons-material/Build'
import { useTranslation } from 'react-i18next'
import {
  getOpenThermLogs,
  getOpenThermCapabilities,
  getOpenthermGateways,
  discoverOpenThermCapabilities,
  clearOpenThermLogs,
  getOpenThermSensorStates,
} from '../api'

interface OpenThermLog {
  timestamp: string
  event_type: string
  data: any
  message?: string
}

export default function OpenThermLogger() {
  const { t } = useTranslation()
  const [logs, setLogs] = useState<OpenThermLog[]>([])
  const [capabilities, setCapabilities] = useState<any>(null)
  const [sensorStates, setSensorStates] = useState<any>(null)
  const [gatewayPresent, setGatewayPresent] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchLogs = async () => {
    try {
      const data = await getOpenThermLogs(100) // Last 100 logs
      setLogs(data.logs)
      setError(null)
    } catch (err) {
      setError(t('opentherm.error.fetchLogs', 'Failed to load OpenTherm logs'))
      console.error(err)
    }
  }

  const fetchSensorStates = async () => {
    try {
      // Check for configured OT gateways; if none, skip sensor state polling to avoid 404 noise
      const gateways = await getOpenthermGateways()
      if (!gateways || gateways.length === 0) {
        setGatewayPresent(false)
        setSensorStates(null)
        setAutoRefresh(false)
        return
      }
      setGatewayPresent(true)
      const data = await getOpenThermSensorStates()
      setSensorStates(data)
    } catch (err) {
      console.error('Failed to load sensor states:', err)
    }
  }

  const fetchCapabilities = async () => {
    try {
      const data = await getOpenThermCapabilities()
      setCapabilities(data)
    } catch (err) {
      console.error('Failed to load capabilities:', err)
    }
  }

  const handleDiscoverCapabilities = async () => {
    try {
      const data = await discoverOpenThermCapabilities()
      setCapabilities(data)
      setError(null)
    } catch (err) {
      setError(t('opentherm.error.discover', 'Failed to discover gateway capabilities'))
      console.error(err)
    }
  }

  const handleClearLogs = async () => {
    try {
      await clearOpenThermLogs()
      setLogs([])
      setError(null)
    } catch (err) {
      setError(t('opentherm.error.clearLogs', 'Failed to clear logs'))
      console.error(err)
    }
  }

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedRows(newExpanded)
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchLogs(), fetchCapabilities(), fetchSensorStates()])
      setLoading(false)
    }
    loadData()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchLogs()
      fetchSensorStates()
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [autoRefresh])

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'boiler_control':
        return <FireplaceIcon fontSize="small" />
      case 'zone_demand':
        return <HomeIcon fontSize="small" />
      case 'modulation':
        return <ThermostatIcon fontSize="small" />
      case 'gateway_info':
        return <InfoIcon fontSize="small" />
      default:
        return null
    }
  }

  const getEventColor = (eventType: string, data: any) => {
    switch (eventType) {
      case 'boiler_control':
        return data.state === 'ON' ? 'success' : 'default'
      case 'zone_demand':
        return data.heating ? 'warning' : 'default'
      case 'modulation':
        return data.flame_on ? 'error' : 'default'
      default:
        return 'info'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Stack spacing={3}>
      {/* Header Controls */}
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            {t('opentherm.title', 'OpenTherm Gateway Monitor')}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchLogs}
              variant="outlined"
            >
              {t('common.refresh', 'Refresh')}
            </Button>
            <Button
              size="small"
              onClick={handleDiscoverCapabilities}
              variant="outlined"
            >
              {t('opentherm.discoverCapabilities', 'Discover Capabilities')}
            </Button>
            <Button
              size="small"
              startIcon={<DeleteIcon />}
              onClick={handleClearLogs}
              color="error"
              variant="outlined"
            >
              {t('common.clear', 'Clear')}
            </Button>
          </Stack>
        </Stack>

        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <Chip
            label={`${t('opentherm.autoRefresh', 'Auto-refresh')}: ${autoRefresh ? 'ON' : 'OFF'}`}
            color={autoRefresh ? 'success' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            size="small"
          />
          <Chip
            label={`${logs.length} ${t('opentherm.logs', 'logs')}`}
            size="small"
          />
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {gatewayPresent === false && (
        <Alert severity="info" sx={{ mt: 1 }}>
          {t('opentherm.noGateways', 'No OpenTherm gateways found. Please add the OpenTherm Gateway integration in Home Assistant.')}
        </Alert>
      )}

      {/* Live Sensor Status Dashboard */}
      {sensorStates && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom sx={{ mb: 2 }}>
            {t('opentherm.liveStatus', 'Live Boiler Status')}
          </Typography>
          <Grid container spacing={2}>
            {/* Control Setpoint */}
            {sensorStates.control_setpoint !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <ThermostatIcon color="primary" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.controlSetpoint', 'Control Setpoint')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.control_setpoint.toFixed(1)}°C
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Modulation Level */}
            {sensorStates.modulation_level !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <SpeedIcon color="warning" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.modulation', 'Modulation Level')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.modulation_level.toFixed(0)}%
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Flame Status */}
            {sensorStates.flame_on !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <WhatshotIcon color={sensorStates.flame_on ? 'error' : 'disabled'} />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.flameStatus', 'Flame Status')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.flame_on ? 'ON' : 'OFF'}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* CH Water Temperature */}
            {sensorStates.ch_water_temp !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <OpacityIcon color="info" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.chWaterTemp', 'CH Water Temp')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.ch_water_temp.toFixed(1)}°C
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Return Water Temperature */}
            {sensorStates.return_water_temp !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <OpacityIcon color="primary" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.returnWaterTemp', 'Return Water Temp')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.return_water_temp.toFixed(1)}°C
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* CH Pressure */}
            {sensorStates.ch_pressure !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <SpeedIcon color="secondary" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.chPressure', 'CH Pressure')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.ch_pressure.toFixed(2)} bar
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Room Temperature */}
            {sensorStates.room_temp !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <HomeIcon color="success" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.roomTemp', 'Room Temperature')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.room_temp.toFixed(1)}°C
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Room Setpoint */}
            {sensorStates.room_setpoint !== undefined && (
              <Grid item xs={12} sm={6} md={4}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <ThermostatIcon color="action" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('opentherm.roomSetpoint', 'Room Setpoint')}
                        </Typography>
                        <Typography variant="h6">
                          {sensorStates.room_setpoint.toFixed(1)}°C
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>

          {/* Boiler Status & Errors */}
          {(sensorStates.ch_active !== undefined || sensorStates.dhw_active !== undefined ||
            sensorStates.fault || sensorStates.diagnostic || sensorStates.low_water_pressure ||
            sensorStates.gas_fault || sensorStates.air_pressure_fault || sensorStates.water_overtemp ||
            sensorStates.service_required) && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                {t('opentherm.statusAndErrors', 'Boiler Status & Errors')}
              </Typography>
              <Grid container spacing={1}>
                {/* CH Active */}
                {sensorStates.ch_active !== undefined && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={sensorStates.ch_active ? <CheckCircleIcon /> : undefined}
                      label={t('opentherm.chActive', 'CH Active')}
                      color={sensorStates.ch_active ? 'success' : 'default'}
                      variant={sensorStates.ch_active ? 'filled' : 'outlined'}
                      size="small"
                    />
                  </Grid>
                )}

                {/* DHW Active */}
                {sensorStates.dhw_active !== undefined && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={sensorStates.dhw_active ? <CheckCircleIcon /> : undefined}
                      label={t('opentherm.dhwActive', 'Hot Water Active')}
                      color={sensorStates.dhw_active ? 'info' : 'default'}
                      variant={sensorStates.dhw_active ? 'filled' : 'outlined'}
                      size="small"
                    />
                  </Grid>
                )}

                {/* Fault */}
                {sensorStates.fault && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<ErrorIcon />}
                      label={t('opentherm.fault', 'FAULT')}
                      color="error"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Diagnostic */}
                {sensorStates.diagnostic && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<WarningIcon />}
                      label={t('opentherm.diagnostic', 'Diagnostic')}
                      color="warning"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Low Water Pressure */}
                {sensorStates.low_water_pressure && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<ErrorIcon />}
                      label={t('opentherm.lowWaterPressure', 'Low Water Pressure')}
                      color="error"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Gas Fault */}
                {sensorStates.gas_fault && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<ErrorIcon />}
                      label={t('opentherm.gasFault', 'Gas Fault')}
                      color="error"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Air Pressure Fault */}
                {sensorStates.air_pressure_fault && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<ErrorIcon />}
                      label={t('opentherm.airPressureFault', 'Air Pressure Fault')}
                      color="error"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Water Overtemperature */}
                {sensorStates.water_overtemp && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<ErrorIcon />}
                      label={t('opentherm.waterOvertemp', 'Water Overtemp')}
                      color="error"
                      size="small"
                    />
                  </Grid>
                )}

                {/* Service Required */}
                {sensorStates.service_required && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Chip
                      icon={<BuildIcon />}
                      label={t('opentherm.serviceRequired', 'Service Required')}
                      color="warning"
                      size="small"
                    />
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </Paper>
      )}

      {/* Gateway Capabilities */}
      {capabilities?.available && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            {t('opentherm.capabilities', 'Gateway Capabilities')}
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {capabilities.attributes && Object.entries(capabilities.attributes).map(([key, value]: [string, any]) => (
              <Chip
                key={key}
                label={`${key}: ${typeof value === 'boolean' ? (value ? 'ON' : 'OFF') : value}`}
                size="small"
                variant="outlined"
              />
            ))}
          </Stack>
        </Paper>
      )}

      {/* Logs Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell width={30}></TableCell>
              <TableCell>{t('opentherm.table.time', 'Time')}</TableCell>
              <TableCell>{t('opentherm.table.type', 'Type')}</TableCell>
              <TableCell>{t('opentherm.table.message', 'Message')}</TableCell>
              <TableCell align="right">{t('opentherm.table.details', 'Details')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary">
                    {t('opentherm.noLogs', 'No logs available')}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log, index) => (
                <>
                  <TableRow key={index} hover>
                    <TableCell>
                      <IconButton size="small" onClick={() => toggleRow(index)}>
                        {expandedRows.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell>{formatTimestamp(log.timestamp)}</TableCell>
                    <TableCell>
                      <Chip
                        icon={getEventIcon(log.event_type) || undefined}
                        label={log.event_type.replace('_', ' ')}
                        size="small"
                        color={getEventColor(log.event_type, log.data)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{log.message || '-'}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      {log.event_type === 'boiler_control' && (
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          {log.data.setpoint && (
                            <Chip label={`${log.data.setpoint}°C`} size="small" />
                          )}
                          {log.data.num_heating_areas !== undefined && (
                            <Chip
                              label={`${log.data.num_heating_areas} zones`}
                              size="small"
                              color="warning"
                            />
                          )}
                        </Stack>
                      )}
                      {log.event_type === 'modulation' && log.data.modulation_level !== undefined && (
                        <Chip
                          label={`${log.data.modulation_level}%`}
                          size="small"
                          color={log.data.modulation_level > 0 ? 'success' : 'default'}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell colSpan={5} sx={{ py: 0 }}>
                      <Collapse in={expandedRows.has(index)} timeout="auto" unmountOnExit>
                        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
                          <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                            {JSON.stringify(log.data, null, 2)}
                          </pre>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  )
}
