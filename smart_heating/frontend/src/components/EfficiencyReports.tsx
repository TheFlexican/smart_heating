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
  List,
  ListItem,
  ListItemText,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  IconButton,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import WarningIcon from '@mui/icons-material/Warning'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { EfficiencyReport, EfficiencyMetrics } from '../types'
import { getEfficiencyReport, getAllAreasEfficiency } from '../api'

type Period = 'day' | 'week' | 'month' | 'year'

const EfficiencyReports: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [period, setPeriod] = useState<Period>('week')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allAreasReport, setAllAreasReport] = useState<EfficiencyReport | null>(null)
  const [selectedArea, setSelectedArea] = useState<string | null>(null)
  const [areaReport, setAreaReport] = useState<EfficiencyReport | null>(null)

  useEffect(() => {
    loadEfficiencyData()
  }, [period])

  const loadEfficiencyData = async () => {
    setLoading(true)
    setError(null)
    try {
      const allAreas = await getAllAreasEfficiency(period)
      setAllAreasReport(allAreas)
      
      // If an area is selected, load its specific report
      if (selectedArea) {
        const areaData = await getEfficiencyReport(selectedArea, period)
        setAreaReport(areaData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load efficiency data')
    } finally {
      setLoading(false)
    }
  }

  const handleAreaSelect = async (areaId: string) => {
    setSelectedArea(areaId)
    setLoading(true)
    try {
      const areaData = await getEfficiencyReport(areaId, period)
      setAreaReport(areaData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load area efficiency')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'info'
    if (score >= 40) return 'warning'
    return 'error'
  }

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return t('efficiency.scoreExcellent')
    if (score >= 60) return t('efficiency.scoreGood')
    if (score >= 40) return t('efficiency.scoreFair')
    return t('efficiency.scorePoor')
  }

  const renderMetricCard = (title: string, value: string, icon?: React.ReactNode) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h5" component="div">
              {value}
            </Typography>
          </Box>
          {icon && <Box>{icon}</Box>}
        </Box>
      </CardContent>
    </Card>
  )

  const renderAreaMetrics = (metrics: EfficiencyMetrics) => (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              {t('efficiency.energyScore')}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h4" component="div">
                {metrics.energy_score.toFixed(0)}
              </Typography>
              <Chip
                label={getScoreLabel(metrics.energy_score)}
                color={getScoreColor(metrics.energy_score) as any}
                size="small"
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={metrics.energy_score}
              color={getScoreColor(metrics.energy_score) as any}
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        {renderMetricCard(
          t('efficiency.heatingTime'),
          `${metrics.heating_time_percentage.toFixed(1)}%`
        )}
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        {renderMetricCard(
          t('efficiency.heatingCycles'),
          metrics.heating_cycles.toString()
        )}
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        {renderMetricCard(
          t('efficiency.tempDelta'),
          `${metrics.avg_temp_delta.toFixed(1)}°C`
        )}
      </Grid>
    </Grid>
  )

  const renderRecommendations = (recommendations: string[]) => {
    if (recommendations.length === 0) {
      return (
        <Alert severity="success" icon={<CheckCircleIcon />}>
          {t('efficiency.recOptimal')}
        </Alert>
      )
    }

    return (
      <List>
        {recommendations.map((rec, index) => (
          <ListItem key={index}>
            <WarningIcon color="warning" sx={{ mr: 2 }} />
            <ListItemText primary={rec} />
          </ListItem>
        ))}
      </List>
    )
  }

  const renderAllAreasTable = () => {
    if (!allAreasReport || !allAreasReport.area_reports) return null

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('area.area')}</TableCell>
              <TableCell align="right">{t('efficiency.energyScore')}</TableCell>
              <TableCell align="right">{t('efficiency.heatingTime')}</TableCell>
              <TableCell align="right">{t('efficiency.heatingCycles')}</TableCell>
              <TableCell align="right">{t('efficiency.tempDelta')}</TableCell>
              <TableCell>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {allAreasReport.area_reports.map((report) => (
              <TableRow
                key={report.area_id}
                hover
                onClick={() => report.area_id && handleAreaSelect(report.area_id)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell component="th" scope="row">
                  {report.area_name}
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={report.metrics.energy_score.toFixed(0)}
                    color={getScoreColor(report.metrics.energy_score) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  {report.metrics.heating_time_percentage.toFixed(1)}%
                </TableCell>
                <TableCell align="right">{report.metrics.heating_cycles}</TableCell>
                <TableCell align="right">
                  {report.metrics.avg_temp_delta.toFixed(1)}°C
                </TableCell>
                <TableCell>
                  <Button size="small" variant="outlined">
                    {t('efficiency.areaDetails')}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
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
              {t('efficiency.title')}
            </Typography>
            <Typography color="textSecondary">
              {t('efficiency.description')}
            </Typography>
          </Box>
        </Box>
        
        <ButtonGroup variant="outlined">
          <Button
            variant={period === 'day' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('day')}
          >
            {t('efficiency.periodDay')}
          </Button>
          <Button
            variant={period === 'week' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('week')}
          >
            {t('efficiency.periodWeek')}
          </Button>
          <Button
            variant={period === 'month' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('month')}
          >
            {t('efficiency.periodMonth')}
          </Button>
          <Button
            variant={period === 'year' ? 'contained' : 'outlined'}
            onClick={() => setPeriod('year')}
          >
            {t('efficiency.periodYear')}
          </Button>
        </ButtonGroup>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && allAreasReport && (
        <Box>
          {/* Summary Metrics */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            {t('efficiency.allAreas')}
          </Typography>
          {allAreasReport.summary_metrics && renderAreaMetrics(allAreasReport.summary_metrics)}

          {/* All Areas Table */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              {t('efficiency.compareAreas')}
            </Typography>
            {renderAllAreasTable()}
          </Box>

          {/* Selected Area Details */}
          {selectedArea && areaReport && (
            <Box sx={{ mt: 4 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  {areaReport.area_name} - {t('efficiency.areaDetails')}
                </Typography>
                <Button onClick={() => setSelectedArea(null)}>
                  {t('common.back')}
                </Button>
              </Box>
              
              {renderAreaMetrics(areaReport.metrics)}
              
              <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  {t('efficiency.recommendations')}
                </Typography>
                {renderRecommendations(areaReport.recommendations)}
              </Paper>
            </Box>
          )}

          {/* Global Recommendations */}
          {!selectedArea && allAreasReport.recommendations.length > 0 && (
            <Paper sx={{ mt: 4, p: 2 }}>
              <Typography variant="h6" gutterBottom>
                {t('efficiency.recommendations')}
              </Typography>
              {renderRecommendations(allAreasReport.recommendations)}
            </Paper>
          )}
        </Box>
      )}

      {!loading && !error && !allAreasReport && (
        <Alert severity="info">
          {t('efficiency.noData')}
        </Alert>
      )}
    </Box>
  )
}

export default EfficiencyReports
