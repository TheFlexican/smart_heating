import React, { useState, useEffect } from 'react'
import { Alert, Box, Button, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { getVacationMode, disableVacationMode } from '../api'
import { VacationMode } from '../types'

export const VacationModeBanner: React.FC = () => {
  const { t } = useTranslation()
  const [vacationMode, setVacationMode] = useState<VacationMode | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadVacationMode()
    // Refresh every 30 seconds to check for changes
    const interval = setInterval(loadVacationMode, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadVacationMode = async () => {
    try {
      const data = await getVacationMode()
      setVacationMode(data)
    } catch (err) {
      console.error('Failed to load vacation mode:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDisable = async () => {
    try {
      await disableVacationMode()
      await loadVacationMode()
    } catch (err) {
      console.error('Failed to disable vacation mode:', err)
    }
  }

  if (loading || !vacationMode?.enabled) {
    return null
  }

  return (
    <Alert
      severity="info"
      sx={{ mb: 2 }}
      action={
        <Button color="inherit" size="small" onClick={handleDisable}>
          {t('common.disable')}
        </Button>
      }
    >
      <Box>
        <Typography variant="body2" fontWeight="bold">
          {t('vacation.active')}
        </Typography>
        <Typography variant="body2">
          {t('vacation.allAreasSet', { preset: vacationMode.preset_mode })}
          {vacationMode.end_date && (
            <> {t('vacation.until', { date: new Date(vacationMode.end_date).toLocaleDateString() })}</>
          )}
        </Typography>
      </Box>
    </Alert>
  )
}
