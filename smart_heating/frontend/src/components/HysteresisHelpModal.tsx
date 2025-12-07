import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  Divider,
} from '@mui/material'
import { useTranslation } from 'react-i18next'

interface HysteresisHelpModalProps {
  open: boolean
  onClose: () => void
}

export default function HysteresisHelpModal({ open, onClose }: HysteresisHelpModalProps) {
  const { t } = useTranslation()

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t('hysteresisHelp.title')}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {/* What is hysteresis */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('hysteresisHelp.whatIsIt')}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('hysteresisHelp.whatIsItExplanation')}
            </Typography>
          </Box>

          <Divider />

          {/* How it works */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('hysteresisHelp.howItWorks')}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {t('hysteresisHelp.howItWorksExplanation')}
            </Typography>
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                <strong>{t('hysteresisHelp.example')}</strong>
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {t('hysteresisHelp.exampleText')}
              </Typography>
            </Alert>
          </Box>

          <Divider />

          {/* Heating system types */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('hysteresisHelp.heatingSystemTypes')}
            </Typography>
            
            <Box sx={{ ml: 2, mt: 2 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                🔥 {t('hysteresisHelp.radiatorHeating')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('hysteresisHelp.radiatorExplanation')}
              </Typography>
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {t('hysteresisHelp.radiatorRecommendation')}
                </Typography>
              </Alert>

              <Typography variant="subtitle2" color="primary" gutterBottom>
                🌡️ {t('hysteresisHelp.floorHeating')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('hysteresisHelp.floorExplanation')}
              </Typography>
              <Alert severity="success" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  {t('hysteresisHelp.floorRecommendation')}
                </Typography>
              </Alert>
            </Box>
          </Box>

          <Divider />

          {/* Settings guide */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('hysteresisHelp.settingsGuide')}
            </Typography>
            <Box sx={{ ml: 2, mt: 1 }}>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>• {t('hysteresisHelp.globalSetting')}</strong> {t('hysteresisHelp.globalSettingExplanation')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>• {t('hysteresisHelp.areaSetting')}</strong> {t('hysteresisHelp.areaSettingExplanation')}
              </Typography>
            </Box>
          </Box>

          <Divider />

          {/* Recommendations */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {t('hysteresisHelp.recommendations')}
            </Typography>
            <Box sx={{ ml: 2, mt: 1 }}>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>0.1-0.3°C:</strong> {t('hysteresisHelp.veryLowRange')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>0.5°C:</strong> {t('hysteresisHelp.balancedRange')}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>1.0-2.0°C:</strong> {t('hysteresisHelp.highRange')}
              </Typography>
            </Box>
          </Box>

          <Alert severity="info" sx={{ mt: 1 }}>
            <Typography variant="body2">
              <strong>💡 {t('hysteresisHelp.boostTip')}</strong> {t('hysteresisHelp.boostTipText')}
            </Typography>
          </Alert>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary" variant="contained">
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
