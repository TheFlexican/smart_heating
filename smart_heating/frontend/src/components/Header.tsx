import { AppBar, Toolbar, Typography, Chip, Box, Tooltip, IconButton, Menu, MenuItem } from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import WifiIcon from '@mui/icons-material/Wifi'
import WifiOffIcon from '@mui/icons-material/WifiOff'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'

interface HeaderProps {
  wsConnected?: boolean
}

const Header = ({ wsConnected = false }: HeaderProps) => {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const isGlobalSettings = location.pathname === '/settings/global'
  const [langMenuAnchor, setLangMenuAnchor] = useState<null | HTMLElement>(null)

  const handleLanguageMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLangMenuAnchor(event.currentTarget)
  }

  const handleLanguageMenuClose = () => {
    setLangMenuAnchor(null)
  }

  const handleLanguageChange = (language: string) => {
    i18n.changeLanguage(language)
    handleLanguageMenuClose()
  }

  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{ 
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider'
      }}
    >
      <Toolbar>
        <ThermostatIcon sx={{ mr: 2, color: 'text.secondary' }} />
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ flexGrow: 1, color: 'text.primary' }}
        >
          {t('header.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {!isGlobalSettings && (
            <Tooltip title={t('header.globalSettings')}>
              <IconButton 
                onClick={() => navigate('/settings/global')}
                sx={{ color: 'text.secondary' }}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title={t('header.changeLanguage')}>
            <IconButton 
              onClick={handleLanguageMenuOpen}
              sx={{ color: 'text.secondary' }}
            >
              <LanguageIcon />
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={langMenuAnchor}
            open={Boolean(langMenuAnchor)}
            onClose={handleLanguageMenuClose}
          >
            <MenuItem onClick={() => handleLanguageChange('en')} selected={i18n.language === 'en'}>
              English
            </MenuItem>
            <MenuItem onClick={() => handleLanguageChange('nl')} selected={i18n.language === 'nl'}>
              Nederlands
            </MenuItem>
          </Menu>
          <Tooltip title={wsConnected ? t('header.realtimeActive') : t('header.realtimeInactive')}>
            <Chip
              icon={wsConnected ? <WifiIcon /> : <WifiOffIcon />}
              label={wsConnected ? t('header.connected') : t('header.disconnected')}
              size="small"
              color={wsConnected ? 'success' : 'default'}
              variant="outlined"
              sx={{
                borderColor: wsConnected ? 'success.main' : 'divider',
                color: wsConnected ? 'success.main' : 'text.secondary'
              }}
            />
          </Tooltip>
          <Chip 
            label="v0.1.0" 
            size="small" 
            variant="outlined"
            sx={{ 
              borderColor: 'divider',
              color: 'text.secondary'
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
