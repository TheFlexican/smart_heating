import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Paper,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  IconButton,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { VacationMode } from '../types'
import { getVacationMode, enableVacationMode, disableVacationMode } from '../api'

export const VacationModeSettings: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [vacationMode, setVacationMode] = useState<VacationMode | null>(null)
  const [startDate, setStartDate] = useState<Date | null>(new Date())
  const [endDate, setEndDate] = useState<Date | null>(null)
  const [presetMode, setPresetMode] = useState<string>('away')
  const [minTemp, setMinTemp] = useState<number>(10)
  const [autoDisable, setAutoDisable] = useState<boolean>(true)
  const [frostProtection, setFrostProtection] = useState<boolean>(true)

  useEffect(() => {
    loadVacationMode()
  }, [])

  const loadVacationMode = async (retryCount = 0) => {
    try {
      setLoading(true)
      const data = await getVacationMode()
      setVacationMode(data)
      
      if (data.start_date) {
        setStartDate(new Date(data.start_date))
      }
      if (data.end_date) {
        setEndDate(new Date(data.end_date))
      }
      setPresetMode(data.preset_mode || 'away')
      setMinTemp(data.min_temperature || 10)
      setAutoDisable(data.auto_disable)
      setFrostProtection(data.frost_protection_override)
    } catch (err) {
      // Retry on network errors (common during page visibility changes)
      if (err && typeof err === 'object' && 'code' in err && err.code === 'ERR_NETWORK' && retryCount < 3) {
        console.warn(`Failed to load vacation mode (network error), retrying (${retryCount + 1}/3)...`)
        // Exponential backoff: 500ms, 1s, 2s
        const delay = 500 * Math.pow(2, retryCount)
        setTimeout(() => loadVacationMode(retryCount + 1), delay)
        return
      }
      
      // Show error to user only after retries exhausted
      if (err && typeof err === 'object' && 'code' in err && err.code === 'ERR_NETWORK') {
        console.error('Failed to load vacation mode after retries (network error):', err)
      } else {
        setError(t('errors.loadFailed'))
        console.error('Failed to load vacation mode:', err)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleEnable = async () => {
    try {
      setSaving(true)
      setError(null)

      const config = {
        start_date: startDate ? startDate.toISOString().split('T')[0] : undefined,
        end_date: endDate ? endDate.toISOString().split('T')[0] : undefined,
        preset_mode: presetMode,
        min_temperature: minTemp,
        auto_disable: autoDisable,
        frost_protection_override: frostProtection,
        person_entities: []  // TODO: Add person entity selection
      }

      const data = await enableVacationMode(config)
      setVacationMode(data)
    } catch (err) {
      setError(t('vacation.enableError'))
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const handleDisable = async () => {
    try {
      setSaving(true)
      setError(null)
      const data = await disableVacationMode()
      setVacationMode(data)
    } catch (err) {
      setError(t('vacation.disableError'))
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <IconButton onClick={() => navigate('/')} size="large" color="primary">
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('vacation.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('vacation.description')}
            </Typography>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {vacationMode?.enabled && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2">
                {t('vacation.activeMessage')}
              </Typography>
              {vacationMode.end_date && (
                <Typography variant="body2">
                  {t('vacation.until', { date: new Date(vacationMode.end_date).toLocaleDateString() })}
                </Typography>
              )}
            </Box>
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Date Range */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <DatePicker
              label={t('vacation.startDate')}
              value={startDate}
              onChange={(date) => setStartDate(date)}
              disabled={vacationMode?.enabled || saving}
              slotProps={{ textField: { fullWidth: true } }}
            />
            <DatePicker
              label={t('vacation.endDate')}
              value={endDate}
              onChange={(date) => setEndDate(date)}
              disabled={vacationMode?.enabled || saving}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Box>

          {/* Preset Mode */}
          <FormControl fullWidth disabled={vacationMode?.enabled || saving}>
            <InputLabel>{t('vacation.presetMode')}</InputLabel>
            <Select
              value={presetMode}
              onChange={(e) => setPresetMode(e.target.value)}
              label={t('vacation.presetMode')}
            >
              <MenuItem value="away">{t('presets.away')}</MenuItem>
              <MenuItem value="eco">{t('presets.eco')}</MenuItem>
              <MenuItem value="sleep">{t('presets.sleep')}</MenuItem>
            </Select>
          </FormControl>

          {/* Frost Protection */}
          <FormControlLabel
            control={
              <Switch
                checked={frostProtection}
                onChange={(e) => setFrostProtection(e.target.checked)}
                disabled={vacationMode?.enabled || saving}
              />
            }
            label={t('vacation.frostProtection')}
          />

          {frostProtection && (
            <TextField
              label={t('vacation.minTemperature')}
              type="number"
              value={minTemp}
              onChange={(e) => setMinTemp(parseFloat(e.target.value))}
              disabled={vacationMode?.enabled || saving}
              inputProps={{ min: 5, max: 15, step: 0.5 }}
              fullWidth
            />
          )}

          {/* Auto-disable */}
          <FormControlLabel
            control={
              <Switch
                checked={autoDisable}
                onChange={(e) => setAutoDisable(e.target.checked)}
                disabled={vacationMode?.enabled || saving}
              />
            }
            label={t('vacation.autoDisable')}
          />

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            {!vacationMode?.enabled ? (
              <Button
                variant="contained"
                color="primary"
                onClick={handleEnable}
                disabled={saving}
                fullWidth
              >
                {saving ? t('vacation.enabling') : t('vacation.enableButton')}
              </Button>
            ) : (
              <Button
                variant="contained"
                color="error"
                onClick={handleDisable}
                disabled={saving}
                fullWidth
              >
                {saving ? t('vacation.disabling') : t('vacation.disableButton')}
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </LocalizationProvider>
  )
}
