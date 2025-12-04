import { AppBar, Toolbar, Typography, Box, Chip } from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'

const Header = () => {
  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <ThermostatIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Zone Heater Manager
        </Typography>
        <Chip 
          label="v0.1.0" 
          size="small" 
          sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}
        />
      </Toolbar>
    </AppBar>
  )
}

export default Header
