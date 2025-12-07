import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Chip,
} from '@mui/material'
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
}

const ZoneList = ({ areas, loading, onUpdate, showHidden, onToggleShowHidden }: ZoneListProps) => {
  const { t } = useTranslation()
  
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
    .sort((a, b) => a.name.localeCompare(b.name))

  return (
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
        <Grid container spacing={{ xs: 2, sm: 2, md: 3 }}>
          {visibleAreas.map((area) => (
            <Grid item xs={12} md={6} lg={4} key={area.id}>
              <ZoneCard area={area} onUpdate={onUpdate} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  )
}

export default ZoneList
