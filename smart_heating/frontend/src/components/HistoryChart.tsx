import { useState, useEffect } from 'react'
import { 
  Box, 
  CircularProgress, 
  Alert, 
  ToggleButtonGroup, 
  ToggleButton, 
  TextField,
  Button,
  Stack
} from '@mui/material'
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ComposedChart
} from 'recharts'
import { getHistory } from '../api'

interface HistoryEntry {
  timestamp: string
  current_temperature: number
  target_temperature: number
  state: string
}

interface HistoryChartProps {
  areaId: string
}

const HistoryChart = ({ areaId }: HistoryChartProps) => {
  const [data, setData] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<number>(24)
  const [customRange, setCustomRange] = useState(false)
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')

  const loadHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      
      let result
      if (customRange && startTime && endTime) {
        // Custom time range
        result = await getHistory(areaId, {
          startTime: new Date(startTime).toISOString(),
          endTime: new Date(endTime).toISOString()
        })
      } else {
        // Preset time range
        result = await getHistory(areaId, { hours: timeRange })
      }
      
      setData(result.entries || [])
    } catch (err) {
      console.error('Failed to load history:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
    
    // Refresh every 5 minutes
    const interval = setInterval(loadHistory, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [areaId, timeRange, customRange, startTime, endTime])

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        No history data available yet. Temperature readings will be recorded every 5 minutes.
      </Alert>
    )
  }

  // Format data for chart
  const chartData = data.map(entry => ({
    time: new Date(entry.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }),
    current: entry.current_temperature,
    target: entry.target_temperature,
    // For heating indicator scatter plot
    heatingDot: entry.state === 'heating' ? entry.current_temperature : null,
    // Store state for custom tooltip
    heatingState: entry.state
  }))

  // Custom tooltip to show heating as Active/Inactive
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <Box
          sx={{
            backgroundColor: '#1c1c1c',
            border: '1px solid #2c2c2c',
            borderRadius: '8px',
            padding: '8px 12px',
            color: '#e1e1e1'
          }}
        >
          <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>{data.time}</div>
          <div style={{ color: '#03a9f4' }}>Current: {data.current.toFixed(1)}°C</div>
          <div style={{ color: '#ffc107' }}>Target: {data.target.toFixed(1)}°C</div>
          <div style={{ color: '#f44336' }}>
            Heating: {data.heatingState === 'heating' ? 'Active' : 'Inactive'}
          </div>
        </Box>
      )
    }
    return null
  }

  // Calculate average target temperature for reference line
  const avgTarget = data.length > 0
    ? data.reduce((sum, entry) => sum + entry.target_temperature, 0) / data.length
    : null

  return (
    <Box>
      <Stack spacing={2} sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <ToggleButtonGroup
            value={customRange ? 'custom' : timeRange}
            exclusive
            onChange={(_e, value) => {
              if (value === 'custom') {
                setCustomRange(true)
              } else if (value) {
                setCustomRange(false)
                setTimeRange(value)
              }
            }}
            size="small"
          >
            <ToggleButton value={6}>6h</ToggleButton>
            <ToggleButton value={12}>12h</ToggleButton>
            <ToggleButton value={24}>24h</ToggleButton>
            <ToggleButton value={72}>3d</ToggleButton>
            <ToggleButton value={168}>7d</ToggleButton>
            <ToggleButton value={720}>30d</ToggleButton>
            <ToggleButton value="custom">Custom</ToggleButton>
          </ToggleButtonGroup>
        </Box>
        
        {customRange && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
            <TextField
              label="Start Date & Time"
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
              sx={{ flex: 1 }}
            />
            <TextField
              label="End Date & Time"
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              InputLabelProps={{ shrink: true }}
              size="small"
              sx={{ flex: 1 }}
            />
            <Button 
              variant="contained" 
              onClick={loadHistory}
              disabled={!startTime || !endTime}
            >
              Apply
            </Button>
          </Box>
        )}
      </Stack>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2c2c2c" />
          <XAxis 
            dataKey="time" 
            stroke="#9e9e9e"
            tick={{ fill: '#9e9e9e' }}
          />
          <YAxis 
            stroke="#9e9e9e"
            tick={{ fill: '#9e9e9e' }}
            domain={['dataMin - 2', 'dataMax + 2']}
            label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', fill: '#9e9e9e' }}
          />
          <Tooltip 
            content={<CustomTooltip />}
          />
          <Legend 
            wrapperStyle={{ color: '#e1e1e1' }}
          />
          {avgTarget && (
            <ReferenceLine
              y={avgTarget}
              stroke="#4caf50"
              strokeDasharray="3 3"
              strokeWidth={1}
              label={{
                value: `Avg: ${avgTarget.toFixed(1)}°C`,
                position: 'right',
                fill: '#4caf50',
                fontSize: 12
              }}
            />
          )}
          <Line
            type="monotone"
            dataKey="current"
            stroke="#03a9f4"
            strokeWidth={2}
            dot={false}
            name="Current Temperature"
          />
          <Line
            type="stepAfter"
            dataKey="target"
            stroke="#ffc107"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Target Temperature"
          />
          <Scatter
            dataKey="heatingDot"
            fill="#f44336"
            shape="circle"
            name="Heating Active"
          />
        </ComposedChart>
      </ResponsiveContainer>

      <Box sx={{ mt: 2 }}>
        <Alert severity="info" variant="outlined">
          <strong>Chart Legend:</strong>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li><strong style={{ color: '#03a9f4' }}>Blue line:</strong> Current temperature</li>
            <li><strong style={{ color: '#ffc107' }}>Yellow dashed:</strong> Target temperature</li>
            <li><strong style={{ color: '#f44336' }}>Red dots:</strong> Heating active periods</li>
            <li><strong style={{ color: '#4caf50' }}>Green dashed:</strong> Average target temperature</li>
          </ul>
        </Alert>
      </Box>
    </Box>
  )
}

export default HistoryChart
