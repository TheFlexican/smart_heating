import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Chip,
} from '@mui/material'
import { DragDropContext, Droppable, DropResult } from 'react-beautiful-dnd'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import { useTranslation } from 'react-i18next'
import ZoneCard from './ZoneCard'
import { Zone } from '../types'

interface ZoneListProps {
  areas: Zone[]
  loading: boolean
  onUpdate: () => void
  showHidden: boolean
  onToggleShowHidden: () => void
  onAreasReorder: (areas: Zone[]) => void
}

const ZoneList = ({ areas, loading, onUpdate, showHidden, onToggleShowHidden, onAreasReorder }: ZoneListProps) => {
  const { t } = useTranslation()

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const items = Array.from(visibleAreas)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    // Merge reordered visible areas with hidden areas
    const hiddenAreas = areas.filter(a => a.hidden && !showHidden)
    const newOrder = [...items, ...hiddenAreas]
    onAreasReorder(newOrder)
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  const hiddenCount = areas.filter(a => a.hidden).length
  const visibleAreas = areas
    .filter(area => showHidden || !area.hidden)

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Box>
        <Box
          mb={{ xs: 2, sm: 3 }}
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={1}
        >
          <Box display="flex" alignItems="center" gap={{ xs: 1, sm: 2 }} flexWrap="wrap">
            <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', sm: '2rem' } }}>
              {t('dashboard.zones')}
            </Typography>
            {hiddenCount > 0 && !showHidden && (
              <Chip
                label={t('dashboard.hiddenCount', { count: hiddenCount })}
                size="small"
                color="default"
                variant="outlined"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
            )}
          </Box>
          {hiddenCount > 0 && (
            <Button
              startIcon={showHidden ? <VisibilityOffIcon /> : <VisibilityIcon />}
              onClick={onToggleShowHidden}
              variant="outlined"
              size="small"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              {showHidden ? t('dashboard.hideHiddenAreas') : t('dashboard.showHiddenAreas')}
            </Button>
          )}
        </Box>

        {visibleAreas.length === 0 ? (
          <Alert severity="info">
            {t('dashboard.noAreasFound')}
          </Alert>
        ) : (
          <Droppable droppableId="areas-list" type="AREA">
            {(provided, snapshot) => (
              <Grid
                container
                spacing={{ xs: 2, sm: 2, md: 3 }}
                ref={provided.innerRef}
                {...provided.droppableProps}
                sx={{
                  bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'transparent',
                  transition: 'background-color 0.2s ease',
                  minHeight: 100,
                  borderRadius: 2,
                }}
              >
                {visibleAreas.map((area, index) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={area.id}>
                    <ZoneCard area={area} onUpdate={onUpdate} index={index} />
                  </Grid>
                ))}
                {provided.placeholder}
              </Grid>
            )}
          </Droppable>
        )}
      </Box>
    </DragDropContext>
  )
}

export default ZoneList
