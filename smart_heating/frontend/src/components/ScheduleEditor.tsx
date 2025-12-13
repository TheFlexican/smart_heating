import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Collapse,
  Stack,
  Alert,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import EventIcon from '@mui/icons-material/Event'
import RepeatIcon from '@mui/icons-material/Repeat'
import { Zone, ScheduleEntry } from '../types'
import { addScheduleToZone, removeScheduleFromZone, updateScheduleInZone } from '../api'
import ScheduleEntryDialog from './ScheduleEntryDialog'
import { format, parse } from 'date-fns'

interface ScheduleEditorProps {
  area: Zone
  onUpdate: () => void
}

const DAYS_OF_WEEK: string[] = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const ScheduleEditor = ({ area, onUpdate }: ScheduleEditorProps) => {
  const { t } = useTranslation()
  const [schedules, setSchedules] = useState<ScheduleEntry[]>(area.schedules || [])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingEntry, setEditingEntry] = useState<ScheduleEntry | null>(null)
  const [expandedDays, setExpandedDays] = useState<Record<string, boolean>>({})
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({})

  useEffect(() => {
    setSchedules(area.schedules || [])
  }, [area])

  const handleAddNew = () => {
    setEditingEntry(null)
    setDialogOpen(true)
  }

  const handleEdit = (entry: ScheduleEntry) => {
    setEditingEntry(entry)
    setDialogOpen(true)
  }

  const handleDelete = async (id: string, day?: string) => {
    try {
      const schedule = schedules.find(s => s.id === id)
      // If a specific day is supplied and schedule exists + has >1 days, update days
      if (day && schedule?.days?.length && schedule.days.length > 1) {
        const newDays = schedule.days.filter(d => d !== day)
        await updateScheduleInZone(area.id, id, { days: newDays })
      } else {
        await removeScheduleFromZone(area.id, id)
      }
      onUpdate()
    } catch (error) {
      console.error('Failed to delete schedule:', error)
    }
  }

  const handleSave = async (entry: ScheduleEntry) => {
    try {
      if (editingEntry) {
        // For updates, remove old and add new
        await removeScheduleFromZone(area.id, editingEntry.id)
      }

      await addScheduleToZone(area.id, entry)
      onUpdate()
      setDialogOpen(false)
    } catch (error) {
      console.error('Failed to save schedule:', error)
    }
  }

  const toggleDay = (day: string) => {
    setExpandedDays(prev => ({ ...prev, [day]: !prev[day] }))
  }

  const toggleDate = (date: string) => {
    setExpandedDates(prev => ({ ...prev, [date]: !prev[date] }))
  }

  // Group schedules by type
  const weeklySchedules = schedules.filter(s => !s.date)
  const dateSpecificSchedules = schedules.filter(s => s.date)

  // Group weekly schedules by day
  const getSchedulesForDay = (day: string) => {
    return weeklySchedules
      .filter(s => {
        if (s.days && s.days.length > 0) {
          return s.days.includes(day)
        }
        return s.day === day
      })
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
  }

  // Group date-specific schedules
  const getSchedulesForDate = (date: string) => {
    return dateSpecificSchedules
      .filter(s => s.date === date)
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
  }

  // Get unique dates
  const uniqueDates = [...new Set(dateSpecificSchedules.map(s => s.date!))]
    .sort((a, b) => a.localeCompare(b))
    .reverse() // Most recent first

  const formatScheduleLabel = (schedule: ScheduleEntry) => {
    const timeRange = `${schedule.start_time} - ${schedule.end_time}`
    const value = schedule.preset_mode
      ? t(`presets.${schedule.preset_mode}`, schedule.preset_mode)
      : `${schedule.temperature}°C`
    return `${timeRange}: ${value}`
  }

  const formatDateLabel = (dateStr: string) => {
    try {
      const date = parse(dateStr, 'yyyy-MM-dd', new Date())
      return format(date, 'PPP') // e.g., "Apr 29, 2024"
    } catch {
      return dateStr
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" color="text.primary">
          {t('areaDetail.weeklySchedule', { area: area.name })}
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddNew}
        >
          {t('areaDetail.addSchedule')}
        </Button>
      </Box>

      {/* Date-Specific Schedules Section */}
      {dateSpecificSchedules.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <EventIcon color="primary" />
            <Typography variant="h6" color="text.primary">
              {t('scheduleDialog.dateSpecificSchedules')}
            </Typography>
          </Box>

          <Stack spacing={2}>
            {uniqueDates.map(date => {
              const dateSchedules = getSchedulesForDate(date)
              const isExpanded = expandedDates[date] ?? true

              return (
                <Card key={date} variant="outlined">
                  <CardContent sx={{ pb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" fontWeight="bold" color="text.primary">
                          {formatDateLabel(date)}
                        </Typography>
                        <Chip
                          label={t('scheduleDialog.oneTimeSchedule')}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      </Box>
                      <IconButton size="small" onClick={() => toggleDate(date)}>
                        {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>

                    <Collapse in={isExpanded}>
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {dateSchedules.map(schedule => (
                          <Chip
                            key={schedule.id}
                            label={formatScheduleLabel(schedule)}
                            onDelete={() => handleDelete(schedule.id)}
                            onClick={() => handleEdit(schedule)}
                            color="primary"
                            variant="outlined"
                            deleteIcon={<DeleteIcon />}
                            icon={<EditIcon />}
                          />
                        ))}
                      </Box>
                    </Collapse>
                  </CardContent>
                </Card>
              )
            })}
          </Stack>
        </Box>
      )}

      {/* Weekly Recurring Schedules Section */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <RepeatIcon color="primary" />
          <Typography variant="h6" color="text.primary">
            {t('scheduleDialog.weeklySchedules')}
          </Typography>
        </Box>

        {weeklySchedules.length === 0 && dateSpecificSchedules.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('areaDetail.noSchedulesConfigured')}
          </Alert>
        )}

        <Stack spacing={2}>
          {DAYS_OF_WEEK.map(day => {
            const daySchedules = getSchedulesForDay(day)
            const dayKey = day.toLowerCase() as 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
            const isExpanded = expandedDays[day] ?? true

            return (
              <Card key={day} variant="outlined">
                <CardContent sx={{ pb: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="subtitle1" fontWeight="bold" color="text.primary">
                      {t(`areaDetail.${dayKey}`)}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {daySchedules.length === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          {t('areaDetail.noSchedulesSet')}
                        </Typography>
                      )}
                      {daySchedules.length > 0 && (
                        <>
                          <Chip label={`${daySchedules.length}`} size="small" color="primary" />
                          <IconButton size="small" onClick={() => toggleDay(day)}>
                            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </>
                      )}
                    </Box>
                  </Box>

                  {daySchedules.length > 0 && (
                    <Collapse in={isExpanded}>
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {daySchedules.map(schedule => (
                          <Chip
                            key={schedule.id}
                            label={formatScheduleLabel(schedule)}
                            onDelete={() => handleDelete(schedule.id, day)}
                            onClick={() => handleEdit(schedule)}
                            color="primary"
                            variant="outlined"
                            deleteIcon={<DeleteIcon />}
                            icon={<EditIcon />}
                          />
                        ))}
                      </Box>
                    </Collapse>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </Stack>
      </Box>

      {/* Schedule Entry Dialog */}
      <ScheduleEntryDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
        editingEntry={editingEntry}
      />
    </Box>
  )
}

export default ScheduleEditor
