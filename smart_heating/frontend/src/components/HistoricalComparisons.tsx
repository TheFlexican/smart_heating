import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  ButtonGroup,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Chip,
  IconButton,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { ComparisonResult, MetricDelta } from '../types'
import { getComparison, getCustomComparison } from '../api'

type Period = 'day' | 'week' | 'month' | 'year' | 'custom'

// Helper function to get chip color based on score
const getScoreColor = (score: number): 'success' | 'info' | 'warning' | 'error' => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'info'
  if (score >= 40) return 'warning'
  return 'error'
}

// Helper function to get severity based on delta
const getDeltaSeverity = (delta: MetricDelta): 'success' | 'warning' | 'info' => {
  if (delta.is_improvement) return 'success'
  if (delta.percent_change < -5) return 'warning'
  return 'info'
}

const HistoricalComparisons: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [period, setPeriod] = useState<Period>('week')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [comparison, setComparison] = useState<ComparisonResult | null>(null)

  // Custom date range state
  const [customStartA, setCustomStartA] = useState('')
  const [customEndA, setCustomEndA] = useState('')
  const [customStartB, setCustomStartB] = useState('')
  const [customEndB, setCustomEndB] = useState('')

  useEffect(() => {
    if (period !== 'custom') {
      loadComparison()
    }
  }, [period])

  const loadComparison = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getComparison(period as 'day' | 'week' | 'month' | 'year')
      setComparison(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comparison data')
    } finally {
      setLoading(false)
    }
  }

  const loadCustomComparison = async () => {
    if (!customStartA || !customEndA || !customStartB || !customEndB) {
      setError('Please select all dates')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await getCustomComparison(
        customStartA,
        customEndA,
        customStartB,
        customEndB
      )
      setComparison(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load custom comparison')
    } finally {
      setLoading(false)
    }
  }

  const getDeltaIcon = (delta: MetricDelta) => {
    if (delta.is_improvement) {
      return <TrendingUpIcon color="success" />
    } else if (delta.percent_change < -5) {
      return <TrendingDownIcon color="error" />
    }
    return <TrendingFlatIcon color="disabled" />
  }

  const getDeltaColor = (delta: MetricDelta): 'success' | 'error' | 'default' => {
    if (delta.is_improvement) return 'success'
    if (delta.percent_change < -5) return 'error'
    return 'default'
  }

  const formatDelta = (delta: MetricDelta, isPercentage: boolean = false): string => {
    const sign = delta.change > 0 ? '+' : ''
    const value = isPercentage
      ? `${sign}${delta.change.toFixed(1)}%`
      : `${sign}${delta.change.toFixed(2)}`
    return `${value} (${delta.percent_change > 0 ? '+' : ''}${delta.percent_change.toFixed(1)}%)`
  }

  const renderMetricComparison = (
    label: string,
    currentValue: number,
    previousValue: number,
    delta: MetricDelta,
    unit: string = ''
  ) => (
    <Card>
      <CardContent>
        <Typography color="textSecondary" gutterBottom>
          {label}
        </Typography>

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              {t('comparison.currentPeriod')}
            </Typography>
            <Typography variant="h6">
              {currentValue.toFixed(1)}{unit}
            </Typography>
          </Box>

          <Box textAlign="right">
            <Typography variant="caption" color="textSecondary">
              {t('comparison.previousPeriod')}
            </Typography>
            <Typography variant="h6" color="textSecondary">
              {previousValue.toFixed(1)}{unit}
            </Typography>
          </Box>
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          {getDeltaIcon(delta)}
          <Chip
            size="small"
            label={formatDelta(delta, unit === '%')}
            color={getDeltaColor(delta)}
          />
        </Box>
      </CardContent>
    </Card>
  )

  const renderAreaComparison = (areaComp: any) => (
    <TableRow key={areaComp.area_id}>
      <TableCell component="th" scope="row">
        {areaComp.area_name}
      </TableCell>
      <TableCell align="right">
        <Chip
          size="small"
          label={areaComp.current_metrics.energy_score.toFixed(0)}
          color={getScoreColor(areaComp.current_metrics.energy_score)}
        />
      </TableCell>
      <TableCell align="right">
        <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
          {getDeltaIcon(areaComp.deltas.energy_score)}
          <Typography variant="body2">
            {formatDelta(areaComp.deltas.energy_score)}
          </Typography>
        </Box>
      </TableCell>
      <TableCell align="right">
        {areaComp.current_metrics.heating_time_percentage.toFixed(1)}%
      </TableCell>
      <TableCell align="right">
        <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
          {getDeltaIcon(areaComp.deltas.heating_time)}
          <Typography variant="body2">
            {formatDelta(areaComp.deltas.heating_time, true)}
          </Typography>
        </Box>
      </TableCell>
      <TableCell align="right">
        {areaComp.current_metrics.heating_cycles}
      </TableCell>
      <TableCell align="right">
        <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
          {getDeltaIcon(areaComp.deltas.heating_cycles)}
          <Typography variant="body2">
            {formatDelta(areaComp.deltas.heating_cycles)}
          </Typography>
        </Box>
      </TableCell>
    </TableRow>
  )

  const renderSummary = () => {
    if (!comparison?.summary_delta) return null

    const delta = comparison.summary_delta.energy_score
    let summaryText = ''

    if (delta.is_improvement) {
      summaryText = t('comparison.summaryImproved', {
        percent: Math.abs(delta.percent_change).toFixed(1)
      })
    } else if (delta.percent_change < -5) {
      summaryText = t('comparison.summaryDecreased', {
        percent: Math.abs(delta.percent_change).toFixed(1)
      })
    } else {
      summaryText = t('comparison.summaryStable')
    }

    return (
      <Alert
        severity={getDeltaSeverity(delta)}
        icon={getDeltaIcon(delta)}
      >
        <Typography variant="body1">{summaryText}</Typography>
      </Alert>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/')} size="large" color="primary">
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" gutterBottom>
              {t('comparison.title')}
            </Typography>
            <Typography color="textSecondary">
              {t('comparison.description')}
            </Typography>
          </Box>
        </Box>

        <ButtonGroup variant="outlined">
          <Button
            variant={period === 'day' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('day')}
          >
            {t('comparison.periodDay')}
          </Button>
          <Button
            variant={period === 'week' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('week')}
          >
            {t('comparison.periodWeek')}
          </Button>
          <Button
            variant={period === 'month' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('month')}
          >
            {t('comparison.periodMonth')}
          </Button>
          <Button
            variant={period === 'year' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('year')}
          >
            {t('comparison.periodYear')}
          </Button>
          <Button
            variant={period === 'custom' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('custom')}
          >
            {t('comparison.periodCustom')}
          </Button>
        </ButtonGroup>
      </Box>

      {/* Custom Date Range Selector */}
      {period === 'custom' && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('comparison.customRange')}
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="date"
                label={t('comparison.periodA') + ' - ' + t('comparison.startDate')}
                value={customStartA}
                onChange={(e) => setCustomStartA(e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="date"
                label={t('comparison.periodA') + ' - ' + t('comparison.endDate')}
                value={customEndA}
                onChange={(e) => setCustomEndA(e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="date"
                label={t('comparison.periodB') + ' - ' + t('comparison.startDate')}
                value={customStartB}
                onChange={(e) => setCustomStartB(e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                type="date"
                label={t('comparison.periodB') + ' - ' + t('comparison.endDate')}
                value={customEndB}
                onChange={(e) => setCustomEndB(e.target.value)}
                slotProps={{ inputLabel: { shrink: true } }}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={loadCustomComparison}
                fullWidth
              >
                {t('comparison.compare')}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && comparison && (
        <Box>
          {/* Summary */}
          <Box mb={3}>
            {renderSummary()}
          </Box>

          {/* Overall Metrics Comparison */}
          {comparison.summary_delta && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {t('comparison.summary')}
              </Typography>
              <Grid container spacing={2} mb={4}>
                <Grid item xs={12} sm={6} md={3}>
                  {renderMetricComparison(
                    t('comparison.energyScore'),
                    comparison.current_summary.energy_score,
                    comparison.previous_summary.energy_score,
                    comparison.summary_delta.energy_score
                  )}
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  {renderMetricComparison(
                    t('comparison.heatingTime'),
                    comparison.current_summary.heating_time_percentage,
                    comparison.previous_summary.heating_time_percentage,
                    comparison.summary_delta.heating_time,
                    '%'
                  )}
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  {renderMetricComparison(
                    t('comparison.heatingCycles'),
                    comparison.current_summary.heating_cycles,
                    comparison.previous_summary.heating_cycles,
                    comparison.summary_delta.heating_cycles
                  )}
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  {renderMetricComparison(
                    t('comparison.tempDelta'),
                    comparison.current_summary.avg_temp_delta,
                    comparison.previous_summary.avg_temp_delta,
                    comparison.summary_delta.temp_delta,
                    '°C'
                  )}
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Area-by-Area Comparison */}
          {comparison.area_comparisons && comparison.area_comparisons.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {t('comparison.comparisonTable')}
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('area.area')}</TableCell>
                      <TableCell align="right">{t('comparison.energyScore')}</TableCell>
                      <TableCell align="right">{t('comparison.delta')}</TableCell>
                      <TableCell align="right">{t('comparison.heatingTime')}</TableCell>
                      <TableCell align="right">{t('comparison.delta')}</TableCell>
                      <TableCell align="right">{t('comparison.heatingCycles')}</TableCell>
                      <TableCell align="right">{t('comparison.delta')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {comparison.area_comparisons.map(renderAreaComparison)}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </Box>
      )}

      {!loading && !error && !comparison && period !== 'custom' && (
        <Alert severity="info">
          {t('comparison.noData')}
        </Alert>
      )}
    </Box>
  )
}

export default HistoricalComparisons
