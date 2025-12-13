import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Alert,
  Switch,
  FormControlLabel,
  Grid,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Home as HomeIcon,
  Settings as SettingsIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { getUsers, createUser, updateUser, deleteUser, updateUserSettings } from '../api'
import { UserProfile, UserData, MultiUserSettings } from '../types'

export const UserManagement: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<UserProfile | null>(null)
  const [formData, setFormData] = useState({
    user_id: '',
    name: '',
    person_entity: '',
    priority: 5,
    preset_preferences: {} as { [key: string]: number },
    areas: [] as string[],
  })

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const data = await getUsers()
      setUserData(data)
      setError(null)
    } catch (err) {
      setError(t('users.errorLoading', 'Failed to load users'))
      console.error('Error loading users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenCreateDialog = () => {
    setEditingUser(null)
    setFormData({
      user_id: '',
      name: '',
      person_entity: '',
      priority: 5,
      preset_preferences: {
        home: 21,
        away: 16,
        sleep: 18,
        eco: 19,
        comfort: 22,
        activity: 20,
      },
      areas: [],
    })
    setEditDialogOpen(true)
  }

  const handleOpenEditDialog = (user: UserProfile) => {
    setEditingUser(user)
    setFormData({
      user_id: user.user_id,
      name: user.name,
      person_entity: user.user_id,
      priority: user.priority,
      preset_preferences: { ...user.preset_preferences },
      areas: [...user.areas],
    })
    setEditDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setEditDialogOpen(false)
    setEditingUser(null)
  }

  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        // Update existing user
        const userId = Object.keys(userData?.users || {}).find(
          (key) => userData?.users[key].user_id === editingUser.user_id
        )
        if (userId) {
          await updateUser(userId, {
            name: formData.name,
            preset_preferences: formData.preset_preferences,
            priority: formData.priority,
            areas: formData.areas,
          })
        }
      } else {
        // Create new user
        await createUser({
          user_id: formData.user_id,
          name: formData.name,
          person_entity: formData.person_entity,
          preset_preferences: formData.preset_preferences,
          priority: formData.priority,
          areas: formData.areas,
        })
      }
      await loadUsers()
      handleCloseDialog()
    } catch (err: any) {
      setError(err.response?.data?.error || t('users.errorSaving', 'Failed to save user'))
      console.error('Error saving user:', err)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm(t('users.confirmDelete', 'Are you sure you want to delete this user?'))) {
      return
    }
    try {
      await deleteUser(userId)
      await loadUsers()
    } catch (err: any) {
      setError(err.response?.data?.error || t('users.errorDeleting', 'Failed to delete user'))
      console.error('Error deleting user:', err)
    }
  }

  const handleUpdateSettings = async (newSettings: Partial<MultiUserSettings>) => {
    try {
      await updateUserSettings(newSettings)
      await loadUsers()
      setSettingsDialogOpen(false)
    } catch (err: any) {
      setError(err.response?.data?.error || t('users.errorUpdatingSettings', 'Failed to update settings'))
      console.error('Error updating settings:', err)
    }
  }

  const handlePresetTempChange = (preset: string, value: number) => {
    setFormData({
      ...formData,
      preset_preferences: {
        ...formData.preset_preferences,
        [preset]: value,
      },
    })
  }

  const getUserStatus = (userId: string): 'home' | 'away' => {
    if (!userData?.presence_state) return 'away'
    const userKey = Object.keys(userData.users).find(
      (key) => userData.users[key].user_id === userId
    )
    return userData.presence_state.users_home.includes(userKey || '') ? 'home' : 'away'
  }

  const isActiveUser = (userId: string): boolean => {
    if (!userData?.presence_state) return false
    const userKey = Object.keys(userData.users).find(
      (key) => userData.users[key].user_id === userId
    )
    return userData.presence_state.active_user === userKey
  }

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>{t('common.loading', 'Loading...')}</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 2,
          borderRadius: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <IconButton onClick={() => navigate('/')} edge="start">
          <ArrowBackIcon />
        </IconButton>
        <PersonIcon />
        <Typography variant="h6">
          {t('users.title', 'User Management')}
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="outlined"
          startIcon={<SettingsIcon />}
          onClick={() => setSettingsDialogOpen(true)}
        >
          {t('users.settings', 'Settings')}
        </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenCreateDialog}
        >
          {t('users.addUser', 'Add User')}
        </Button>
      </Paper>

      <Box sx={{ px: 3 }}>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {userData?.presence_state && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('users.presenceStatus', 'Presence Status')}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Chip
              icon={<HomeIcon />}
              label={t('users.usersHome', `${userData.presence_state.users_home.length} users home`)}
              color={userData.presence_state.users_home.length > 0 ? 'success' : 'default'}
            />
            {userData.presence_state.active_user && (
              <Chip
                label={t(
                  'users.activeUser',
                  `Active: ${userData.users[userData.presence_state.active_user]?.name || 'Unknown'}`
                )}
                color="primary"
              />
            )}
            <Chip
              label={t(`users.mode.${userData.presence_state.combined_mode}`, userData.presence_state.combined_mode)}
            />
          </Stack>
        </Paper>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('users.status', 'Status')}</TableCell>
              <TableCell>{t('users.name', 'Name')}</TableCell>
              <TableCell>{t('users.personEntity', 'Person Entity')}</TableCell>
              <TableCell>{t('users.priority', 'Priority')}</TableCell>
              <TableCell>{t('users.presetPreferences', 'Preset Preferences')}</TableCell>
              <TableCell>{t('common.actions', 'Actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {userData && Object.entries(userData.users).map(([userId, user]) => (
              <TableRow key={userId}>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Chip
                      size="small"
                      label={getUserStatus(user.user_id)}
                      color={getUserStatus(user.user_id) === 'home' ? 'success' : 'default'}
                    />
                    {isActiveUser(user.user_id) && (
                      <Chip size="small" label={t('users.active', 'Active')} color="primary" />
                    )}
                  </Stack>
                </TableCell>
                <TableCell>{user.name}</TableCell>
                <TableCell>{user.user_id}</TableCell>
                <TableCell>{user.priority}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5} flexWrap="wrap">
                    {Object.entries(user.preset_preferences).map(([preset, temp]) => (
                      <Chip
                        key={preset}
                        size="small"
                        label={`${preset}: ${temp}°C`}
                      />
                    ))}
                  </Stack>
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleOpenEditDialog(user)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDeleteUser(userId)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {(!userData || Object.keys(userData.users).length === 0) && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  {t('users.noUsers', 'No users configured')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingUser
            ? t('users.editUser', 'Edit User')
            : t('users.createUser', 'Create User')}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('users.userId', 'User ID')}
                value={formData.user_id}
                onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                disabled={!!editingUser}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('users.name', 'Name')}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={t('users.personEntity', 'Person Entity')}
                value={formData.person_entity}
                onChange={(e) => setFormData({ ...formData, person_entity: e.target.value })}
                disabled={!!editingUser}
                required
                helperText="e.g., person.john"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label={t('users.priority', 'Priority (1-10)')}
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: Number.parseInt(e.target.value) })}
                slotProps={{ htmlInput: { min: 1, max: 10 } }}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                {t('users.presetPreferences', 'Preset Preferences')}
              </Typography>
            </Grid>
            {['home', 'away', 'sleep', 'eco', 'comfort', 'activity'].map((preset) => (
              <Grid item xs={6} md={4} key={preset}>
                <TextField
                  fullWidth
                  type="number"
                  label={t(`presets.${preset}`, preset)}
                  value={formData.preset_preferences[preset] || ''}
                  onChange={(e) => handlePresetTempChange(preset, Number.parseFloat(e.target.value))}
                  slotProps={{
                    htmlInput: { step: 0.5 },
                    input: { endAdornment: '°C' }
                  }}
                />
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>{t('common.cancel', 'Cancel')}</Button>
          <Button onClick={handleSaveUser} variant="contained">
            {t('common.save', 'Save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={settingsDialogOpen} onClose={() => setSettingsDialogOpen(false)}>
        <DialogTitle>{t('users.settings', 'Multi-User Settings')}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={userData?.settings.enabled || false}
                  onChange={(e) =>
                    handleUpdateSettings({ enabled: e.target.checked })
                  }
                />
              }
              label={t('users.enableMultiUser', 'Enable Multi-User Presence Tracking')}
            />
            <FormControl fullWidth>
              <InputLabel>{t('users.strategy', 'Strategy')}</InputLabel>
              <Select
                value={userData?.settings.multi_user_strategy || 'priority'}
                onChange={(e) =>
                  handleUpdateSettings({
                    multi_user_strategy: e.target.value as 'priority' | 'average',
                  })
                }
              >
                <MenuItem value="priority">
                  {t('users.strategyPriority', 'Priority (highest priority user wins)')}
                </MenuItem>
                <MenuItem value="average">
                  {t('users.strategyAverage', 'Average (average all users\' preferences)')}
                </MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>
            {t('common.close', 'Close')}
          </Button>
        </DialogActions>
      </Dialog>
      </Box>
    </Box>
  )
}
