import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
  FormControlLabel,
  Checkbox,
  Paper,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { format, parse } from 'date-fns'
import { ScheduleEntry } from '../types'

interface ScheduleEntryDialogProps {
  open: boolean
  onClose: () => void
  onSave: (entry: ScheduleEntry) => Promise<void>
  editingEntry: ScheduleEntry | null
}

const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const ScheduleEntryDialog = ({
  open,
  onClose,
  onSave,
  editingEntry,
}: ScheduleEntryDialogProps) => {
  const { t } = useTranslation()

  // Schedule type: 'weekly' for recurring, 'date' for specific date
  const [scheduleType, setScheduleType] = useState<'weekly' | 'date'>('weekly')
  const [selectedDays, setSelectedDays] = useState<number[]>([0])
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date())
  const [startTime, setStartTime] = useState('06:00')
  const [endTime, setEndTime] = useState('22:00')
  const [usePreset, setUsePreset] = useState(false)
  const [temperature, setTemperature] = useState(20)
  const [presetMode, setPresetMode] = useState('none')

  useEffect(() => {
    if (open) {
      if (editingEntry) {
        // Populate form with editing data
        setStartTime(editingEntry.start_time)
        setEndTime(editingEntry.end_time)
        setUsePreset(!!editingEntry.preset_mode)
        setTemperature(editingEntry.temperature || 20)
        setPresetMode(editingEntry.preset_mode || 'none')

        if (editingEntry.date) {
          setScheduleType('date')
          setSelectedDate(parse(editingEntry.date, 'yyyy-MM-dd', new Date()))
        } else {
          setScheduleType('weekly')
          if (editingEntry.days && editingEntry.days.length > 0) {
            // editingEntry.days are indices
            setSelectedDays(editingEntry.days as number[])
          } else if (typeof editingEntry.day === 'number') {
            setSelectedDays([editingEntry.day as number])
          }
        }
      } else {
        // Reset to defaults for new entry
        setScheduleType('weekly')
        setSelectedDays([0])
        setSelectedDate(new Date())
        setStartTime('06:00')
        setEndTime('22:00')
        setUsePreset(false)
        setTemperature(20)
        setPresetMode('none')
      }
    }
  }, [open, editingEntry])

  const handleDayToggle = (dayIndex: number) => {
    setSelectedDays(prev =>
      prev.includes(dayIndex)
        ? prev.filter(d => d !== dayIndex)
        : [...prev, dayIndex]
    )
  }

  const handleSelectAllWeekdays = () => {
    setSelectedDays([0, 1, 2, 3, 4])
  }

  const handleSelectWeekend = () => {
    setSelectedDays([5, 6])
  }

  const handleSelectAllDays = () => {
    setSelectedDays([0, 1, 2, 3, 4, 5, 6])
  }

  const handleSave = async () => {
    const entry: ScheduleEntry = {
      id: editingEntry?.id || Date.now().toString(),
      start_time: startTime,
      end_time: endTime,
    }

    // Set schedule type - either weekly recurring or specific date
    if (scheduleType === 'date' && selectedDate) {
      entry.date = format(selectedDate, 'yyyy-MM-dd')
    } else {
      entry.days = selectedDays
    }

    // Set temperature or preset
    if (usePreset && presetMode !== 'none') {
      entry.preset_mode = presetMode
    } else {
      entry.temperature = temperature
    }

    await onSave(entry)
  }

  const isValid = () => {
    if (scheduleType === 'weekly' && selectedDays.length === 0) return false
    if (scheduleType === 'date' && !selectedDate) return false
    return true
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {editingEntry ? t('scheduleDialog.editTitle') : t('scheduleDialog.addTitle')}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
          {/* Schedule Type Toggle */}
          <Box>
            <Typography variant="subtitle2" gutterBottom color="text.secondary">
              {t('scheduleDialog.scheduleType')}
            </Typography>
            <ToggleButtonGroup
              value={scheduleType}
              exclusive
              onChange={(_, value) => value && setScheduleType(value)}
              fullWidth
            >
              <ToggleButton value="weekly">
                {t('scheduleDialog.weeklyRecurring')}
              </ToggleButton>
              <ToggleButton value="date">
                {t('scheduleDialog.specificDate')}
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Day/Date Selection */}
          {scheduleType === 'weekly' ? (
            <Box>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                {t('scheduleDialog.selectDays')}
              </Typography>
              <Paper variant="outlined" sx={{ p: 2 }}>
                {/* Quick selection buttons */}
                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleSelectAllWeekdays}
                  >
                    {t('scheduleDialog.weekdays')}
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleSelectWeekend}
                  >
                    {t('scheduleDialog.weekend')}
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleSelectAllDays}
                  >
                    {t('scheduleDialog.allDays')}
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => setSelectedDays([])}
                  >
                    {t('scheduleDialog.clearSelection')}
                  </Button>
                </Box>

                {/* Day checkboxes */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  {DAYS_OF_WEEK.map((day, idx) => {
                    const dayKey = day.toLowerCase() as 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
                    return (
                      <FormControlLabel
                        key={day}
                        control={
                          <Checkbox
                            checked={selectedDays.includes(idx)}
                            onChange={() => handleDayToggle(idx)}
                          />
                        }
                        label={t(`areaDetail.${dayKey}`)}
                      />
                    )
                  })}
                </Box>

                {/* Selected days preview */}
                {selectedDays.length > 0 && (
                  <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary">
                      {t('scheduleDialog.selectedDaysCount', { count: selectedDays.length })}:
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                      {selectedDays.map(dayIdx => (
                        <Chip key={dayIdx} label={DAYS_OF_WEEK[dayIdx]} size="small" color="primary" />
                      ))}
                    </Box>
                  </Box>
                )}
              </Paper>
            </Box>
          ) : (
            <Box>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                {t('scheduleDialog.selectDate')}
              </Typography>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label={t('scheduleDialog.date')}
                  value={selectedDate}
                  onChange={(newValue) => setSelectedDate(newValue)}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      helperText: t('scheduleDialog.dateHelperText'),
                    },
                  }}
                />
              </LocalizationProvider>
            </Box>
          )}

          {/* Time Selection */}
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label={t('scheduleDialog.startTime')}
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
              helperText={t('scheduleDialog.spanHelperText')}
            />

            <TextField
              label={t('scheduleDialog.endTime')}
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              fullWidth
            />
          </Box>

          {/* Temperature/Preset Mode Selection */}
          <FormControl fullWidth>
            <InputLabel>{t('scheduleDialog.mode')}</InputLabel>
            <Select
              value={usePreset ? 'preset' : 'temperature'}
              label={t('scheduleDialog.mode')}
              onChange={(e) => setUsePreset(e.target.value === 'preset')}
            >
              <MenuItem value="temperature">{t('scheduleDialog.fixedTemperature')}</MenuItem>
              <MenuItem value="preset">{t('scheduleDialog.presetMode')}</MenuItem>
            </Select>
          </FormControl>

          {usePreset ? (
            <FormControl fullWidth>
              <InputLabel>{t('scheduleDialog.preset')}</InputLabel>
              <Select
                value={presetMode}
                label={t('scheduleDialog.preset')}
                onChange={(e) => setPresetMode(e.target.value)}
              >
                <MenuItem value="none">{t('scheduleDialog.presetNone')}</MenuItem>
                <MenuItem value="eco">{t('scheduleDialog.presetEco')}</MenuItem>
                <MenuItem value="away">{t('scheduleDialog.presetAway')}</MenuItem>
                <MenuItem value="comfort">{t('scheduleDialog.presetComfort')}</MenuItem>
                <MenuItem value="home">{t('scheduleDialog.presetHome')}</MenuItem>
                <MenuItem value="sleep">{t('scheduleDialog.presetSleep')}</MenuItem>
                <MenuItem value="activity">{t('scheduleDialog.presetActivity')}</MenuItem>
              </Select>
            </FormControl>
          ) : (
            <TextField
              label={t('scheduleDialog.temperature')}
              type="number"
              value={temperature}
              onChange={(e) => setTemperature(Number.parseFloat(e.target.value))}
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: { min: 5, max: 30, step: 0.5 }
              }}
              fullWidth
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button onClick={handleSave} variant="contained" disabled={!isValid()}>
          {t('common.save')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ScheduleEntryDialog
