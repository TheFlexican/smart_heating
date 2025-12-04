import { useState } from 'react'
import {
  Box,
  Button,
  Grid,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ZoneCard from './ZoneCard'
import CreateZoneDialog from './CreateZoneDialog'
import { Zone } from '../types'

interface AreaListProps {
  zones: Area[]
  loading: boolean
  onUpdate: () => void
}

const ZoneList = ({ zones, loading, onUpdate }: AreaListProps) => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Zones
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Zone
        </Button>
      </Box>

      {zones.length === 0 ? (
        <Alert severity="info">
          No zones configured yet. Click "Create Zone" to get started!
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {zones.map((zone) => (
            <Grid item xs={12} md={6} lg={4} key={zone.id}>
              <ZoneCard zone={zone} onUpdate={onUpdate} />
            </Grid>
          ))}
        </Grid>
      )}

      <CreateZoneDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={onUpdate}
      />
    </Box>
  )
}

export default ZoneList
