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
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  const hiddenCount = areas.filter(a => a.hidden).length
  const visibleAreas = areas.filter(area => showHidden || !area.hidden)

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h4">
            Zones
          </Typography>
          {hiddenCount > 0 && !showHidden && (
            <Chip 
              label={`${hiddenCount} hidden`} 
              size="small" 
              color="default"
              variant="outlined"
            />
          )}
        </Box>
        {hiddenCount > 0 && (
          <Button
            startIcon={showHidden ? <VisibilityOffIcon /> : <VisibilityIcon />}
            onClick={onToggleShowHidden}
            variant="outlined"
            size="small"
          >
            {showHidden ? 'Hide Hidden Areas' : 'Show Hidden Areas'}
          </Button>
        )}
      </Box>

      {visibleAreas.length === 0 ? (
        <Alert severity="info">
          No areas found. Please configure areas in Home Assistant first (Settings → Areas & Zones → Areas).
        </Alert>
      ) : (
        <Grid container spacing={3}>
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
