import { AppBar, Toolbar, Typography, Chip, Box, Tooltip, IconButton, Menu, MenuItem } from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import WifiIcon from '@mui/icons-material/Wifi'
import WifiOffIcon from '@mui/icons-material/WifiOff'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import PeopleIcon from '@mui/icons-material/People'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
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
  const isSettings = location.pathname.startsWith('/settings/')
  const [langMenuAnchor, setLangMenuAnchor] = useState<null | HTMLElement>(null)
  const [settingsMenuAnchor, setSettingsMenuAnchor] = useState<null | HTMLElement>(null)
  const [analyticsMenuAnchor, setAnalyticsMenuAnchor] = useState<null | HTMLElement>(null)

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

  const handleSettingsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setSettingsMenuAnchor(event.currentTarget)
  }

  const handleSettingsMenuClose = () => {
    setSettingsMenuAnchor(null)
  }

  const handleNavigateSettings = (path: string) => {
    navigate(path)
    handleSettingsMenuClose()
  }

  const handleAnalyticsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnalyticsMenuAnchor(event.currentTarget)
  }

  const handleAnalyticsMenuClose = () => {
    setAnalyticsMenuAnchor(null)
  }

  const handleNavigateAnalytics = (path: string) => {
    navigate(path)
    handleAnalyticsMenuClose()
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
      <Toolbar sx={{ gap: { xs: 1, sm: 2 } }}>
        <ThermostatIcon sx={{ color: 'primary.main', fontSize: { xs: 28, sm: 32 } }} />
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            fontSize: { xs: '1rem', sm: '1.25rem' },
            cursor: 'pointer'
          }}
          onClick={() => navigate('/')}
        >
          {t('header.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: { xs: 0.5, sm: 1 }, alignItems: 'center' }}>
          {!isSettings && (
            <>
              <Tooltip title={t('header.analytics', 'Analytics')}>
                <IconButton
                  onClick={handleAnalyticsMenuOpen}
                  sx={{
                    color: 'text.secondary',
                    p: { xs: 0.5, sm: 1 }
                  }}
                >
                  <AnalyticsIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('header.settings', 'Settings')}>
                <IconButton
                  onClick={handleSettingsMenuOpen}
                  sx={{
                    color: 'text.secondary',
                    p: { xs: 0.5, sm: 1 }
                  }}
                >
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
            </>
          )}
          <Menu
            anchorEl={analyticsMenuAnchor}
            open={Boolean(analyticsMenuAnchor)}
            onClose={handleAnalyticsMenuClose}
          >
            <MenuItem onClick={() => handleNavigateAnalytics('/analytics/efficiency')}>
              <TrendingUpIcon sx={{ mr: 1 }} />
              {t('efficiency.title', 'Efficiency Reports')}
            </MenuItem>
            <MenuItem onClick={() => handleNavigateAnalytics('/analytics/comparison')}>
              <CompareArrowsIcon sx={{ mr: 1 }} />
              {t('comparison.title', 'Historical Comparisons')}
            </MenuItem>
          </Menu>
          <Menu
            anchorEl={settingsMenuAnchor}
            open={Boolean(settingsMenuAnchor)}
            onClose={handleSettingsMenuClose}
          >
            <MenuItem onClick={() => handleNavigateSettings('/settings/global')}>
              <SettingsIcon sx={{ mr: 1 }} />
              {t('header.globalSettings', 'Global Settings')}
            </MenuItem>
            <MenuItem onClick={() => handleNavigateSettings('/settings/users')}>
              <PeopleIcon sx={{ mr: 1 }} />
              {t('header.userManagement', 'User Management')}
            </MenuItem>
          </Menu>
          <Tooltip title={t('header.changeLanguage')}>
            <IconButton
              onClick={handleLanguageMenuOpen}
              sx={{
                color: 'text.secondary',
                p: { xs: 0.5, sm: 1 }
              }}
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
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Chip
                icon={wsConnected ? <WifiIcon /> : <WifiOffIcon />}
                label={wsConnected ? t('header.connected') : t('header.disconnected')}
                size="small"
                color={wsConnected ? 'success' : 'default'}
                variant="outlined"
                sx={{
                  borderColor: wsConnected ? 'success.main' : 'divider',
                  color: wsConnected ? 'success.main' : 'text.secondary',
                  display: { xs: 'none', sm: 'flex' }
                }}
              />
              <Box sx={{ display: { xs: 'flex', sm: 'none' } }}>
                {wsConnected ? <WifiIcon color="success" /> : <WifiOffIcon color="disabled" />}
              </Box>
            </Box>
          </Tooltip>
          <Chip
            label="v0.5.14"
            size="small"
            variant="outlined"
            sx={{
              borderColor: 'divider',
              color: 'text.secondary',
              display: { xs: 'none', sm: 'flex' }
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
