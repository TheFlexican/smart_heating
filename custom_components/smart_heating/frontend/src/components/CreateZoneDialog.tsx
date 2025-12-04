import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Slider,
  Typography,
  Box
} from '@mui/material'
import { createZone } from '../api'

interface CreateZoneDialogProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

const CreateZoneDialog = ({ open, onClose, onSuccess }: CreateZoneDialogProps) => {
  const [areaName, setZoneName] = useState('')
  const [areaId, setZoneId] = useState('')
  const [temperature, setTemperature] = useState(20)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    try {
      setLoading(true)
      await createZone({
        zone_id: areaId,
        zone_name: areaName,
        temperature
      })
      setZoneName('')
      setZoneId('')
      setTemperature(20)
      onSuccess()
      onClose()
    } catch (error) {
      console.error('Failed to create zone:', error)
      alert('Failed to create zone. Check console for details.')
    } finally {
      setLoading(false)
    }
  }

  const handleNameChange = (value: string) => {
    setZoneName(value)
    // Auto-generate ID from name
    setZoneId(value.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, ''))
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Zone</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            label="Zone Name"
            value={areaName}
            onChange={(e) => handleNameChange(e.target.value)}
            fullWidth
            required
            placeholder="e.g., Living Room"
          />
          
          <TextField
            label="Zone ID"
            value={areaId}
            onChange={(e) => setZoneId(e.target.value)}
            fullWidth
            required
            helperText="Auto-generated from name, or customize"
            placeholder="e.g., living_room"
          />

          <Box>
            <Typography gutterBottom>
              Initial Temperature: {temperature}°C
            </Typography>
            <Slider
              value={temperature}
              onChange={(_e, value) => setTemperature(value as number)}
              min={5}
              max={30}
              step={0.5}
              marks={[
                { value: 5, label: '5°' },
                { value: 20, label: '20°' },
                { value: 30, label: '30°' }
              ]}
              valueLabelDisplay="auto"
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!areaName || !areaId || loading}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default CreateZoneDialog
