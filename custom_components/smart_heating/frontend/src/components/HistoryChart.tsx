import { useState, useEffect } from 'react'
import { Box, CircularProgress, Alert, ToggleButtonGroup, ToggleButton } from '@mui/material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'

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

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`/api/smart_heating/areas/${areaId}/history?hours=${timeRange}`)
        if (!response.ok) {
          throw new Error('Failed to load history')
        }
        
        const result = await response.json()
        setData(result.entries || [])
      } catch (err) {
        console.error('Failed to load history:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    loadHistory()
    
    // Refresh every 5 minutes
    const interval = setInterval(loadHistory, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [areaId, timeRange])

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
    heating: entry.state === 'heating' ? entry.current_temperature : null
  }))

  // Calculate average target temperature for reference line
  const avgTarget = data.length > 0
    ? data.reduce((sum, entry) => sum + entry.target_temperature, 0) / data.length
    : null

  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <ToggleButtonGroup
          value={timeRange}
          exclusive
          onChange={(_e, value) => value && setTimeRange(value)}
          size="small"
        >
          <ToggleButton value={6}>6h</ToggleButton>
          <ToggleButton value={12}>12h</ToggleButton>
          <ToggleButton value={24}>24h</ToggleButton>
          <ToggleButton value={72}>3d</ToggleButton>
          <ToggleButton value={168}>7d</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
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
            contentStyle={{
              backgroundColor: '#1c1c1c',
              border: '1px solid #2c2c2c',
              borderRadius: '8px'
            }}
            labelStyle={{ color: '#e1e1e1' }}
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
          <Line
            type="monotone"
            dataKey="heating"
            stroke="#f44336"
            strokeWidth={3}
            dot={{ r: 3 }}
            connectNulls={false}
            name="Heating Active"
          />
        </LineChart>
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
