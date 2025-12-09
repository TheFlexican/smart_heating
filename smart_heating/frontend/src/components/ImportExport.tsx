import { useState } from 'react'
import {
  Box,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from '@mui/material'
import {
  Download as DownloadIcon,
  Upload as UploadIcon,
  Backup as BackupIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { importConfig, validateConfig } from '../api'

interface ImportPreview {
  valid: boolean
  version?: string
  export_date?: string
  areas_to_create?: number
  areas_to_update?: number
  global_settings_included?: boolean
  vacation_mode_included?: boolean
  error?: string
}

interface ImportResult {
  success: boolean
  message: string
  changes?: {
    areas_created: number
    areas_updated: number
    areas_deleted: number
    global_settings_updated: boolean
    vacation_mode_updated: boolean
  }
  error?: string
}

const ImportExport = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [importData, setImportData] = useState<any>(null)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)

  const handleExport = async () => {
    try {
      setLoading(true)
      setError(null)
      setSuccess(null)

      const response = await fetch('/api/smart_heating/export')
      if (!response.ok) {
        throw new Error('Failed to export configuration')
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'smart_heating_backup.json'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/)
        if (match) {
          filename = match[1]
        }
      }

      // Download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccess(t('importExport.exportSuccess'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setLoading(true)
      setError(null)
      setSuccess(null)

      // Read file content
      const text = await file.text()
      const data = JSON.parse(text)
      setImportData(data)

      // Validate configuration
      const previewData = await validateConfig(data)
      setPreview(previewData)
      setShowPreviewDialog(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to read file')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmImport = async () => {
    if (!importData) return

    try {
      setLoading(true)
      setError(null)
      setSuccess(null)
      setShowPreviewDialog(false)

      const result: ImportResult = await importConfig(importData)

      if (result.success) {
        const changes = result.changes
        let message = t('importExport.importSuccess') + '\\n'
        if (changes) {
          if (changes.areas_created > 0) {
            message += `\\n• ${changes.areas_created} ${t('importExport.areasCreated')}`
          }
          if (changes.areas_updated > 0) {
            message += `\\n• ${changes.areas_updated} ${t('importExport.areasUpdated')}`
          }
          if (changes.global_settings_updated) {
            message += `\\n• ${t('importExport.globalSettingsUpdated')}`
          }
          if (changes.vacation_mode_updated) {
            message += `\\n• ${t('importExport.vacationModeUpdated')}`
          }
        }
        setSuccess(message)

        // Reload page after 2 seconds to reflect changes
        setTimeout(() => {
          window.location.reload()
        }, 2000)
      } else {
        setError(result.error || 'Import failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setLoading(false)
      setImportData(null)
      setPreview(null)
    }
  }

  const handleCancelImport = () => {
    setShowPreviewDialog(false)
    setImportData(null)
    setPreview(null)
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <IconButton onClick={() => navigate('/')} size="large" color="primary">
          <ArrowBackIcon />
          </IconButton>
        <Typography variant="body2" color="text.secondary">
          {t('importExport.description')}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success.split('\\n').map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {/* Export Button */}
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
          onClick={handleExport}
          disabled={loading}
        >
          {t('importExport.exportButton')}
        </Button>

        {/* Import Button */}
        <Button
          variant="outlined"
          component="label"
          startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
          disabled={loading}
        >
          {t('importExport.importButton')}
          <input
            type="file"
            accept=".json"
            hidden
            onChange={handleFileSelect}
          />
        </Button>
      </Box>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <BackupIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
          {t('importExport.backupInfo')}
        </Typography>
      </Alert>

      {/* Preview Dialog */}
      <Dialog
        open={showPreviewDialog}
        onClose={handleCancelImport}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('importExport.previewTitle')}</DialogTitle>
        <DialogContent>
          {preview && preview.valid ? (
            <>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {t('importExport.previewDescription')}
              </Typography>
              <List dense>
                {preview.version && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.version')}
                      secondary={preview.version}
                    />
                  </ListItem>
                )}
                {preview.export_date && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.exportDate')}
                      secondary={new Date(preview.export_date).toLocaleString()}
                    />
                  </ListItem>
                )}
                {(preview.areas_to_create ?? 0) > 0 && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.areasToCreate')}
                      secondary={preview.areas_to_create}
                    />
                  </ListItem>
                )}
                {(preview.areas_to_update ?? 0) > 0 && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.areasToUpdate')}
                      secondary={preview.areas_to_update}
                    />
                  </ListItem>
                )}
                {preview.global_settings_included && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.globalSettings')}
                      secondary={t('importExport.willBeUpdated')}
                    />
                  </ListItem>
                )}
                {preview.vacation_mode_included && (
                  <ListItem>
                    <ListItemText
                      primary={t('importExport.vacationMode')}
                      secondary={t('importExport.willBeUpdated')}
                    />
                  </ListItem>
                )}
              </List>
              <Alert severity="warning" sx={{ mt: 2 }}>
                {t('importExport.backupWarning')}
              </Alert>
            </>
          ) : (
            <Alert severity="error">
              {preview?.error || t('importExport.invalidConfig')}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelImport}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleConfirmImport}
            variant="contained"
            disabled={!preview?.valid || loading}
          >
            {loading ? <CircularProgress size={20} /> : t('importExport.confirmImport')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ImportExport
