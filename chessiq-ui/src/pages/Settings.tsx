import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Navbar from '../components/navbar/Navbar'
import { settingsApi, type UserSettings, type ChangePasswordData } from '../services/api'
import './settings.css'

type TabType = 'game' | 'account' | 'security'

function Settings() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [activeTab, setActiveTab] = useState<TabType>('game')
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  
  const [gameSettings, setGameSettings] = useState({
    showLegalMoves: true,
    highlightLastMove: true,
  })
  
  const [accountSettings, setAccountSettings] = useState({
    displayName: '',
    language: 'en',
    timezone: 'UTC',
  })
  
  const [passwordForm, setPasswordForm] = useState<ChangePasswordData>({
    currentPassword: '',
    newPassword: '',
  })
  const [confirmPassword, setConfirmPassword] = useState('')

  // Redirect if not logged in
  useEffect(() => {
    if (!user) {
      navigate('/signin')
    }
  }, [user, navigate])

  // Fetch settings
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await settingsApi.get()
        setSettings(data)
        setGameSettings({
          showLegalMoves: data.game.showLegalMoves,
          highlightLastMove: data.game.highlightLastMove,
        })
        setAccountSettings({
          displayName: data.general.displayName,
          language: data.general.language,
          timezone: data.general.timezone,
        })
      } catch (err) {
        console.error('Failed to fetch settings:', err)
        setError('Failed to load settings. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    if (user) {
      fetchSettings()
    }
  }, [user])

  const handleGameSettingChange = (key: keyof typeof gameSettings, value: boolean) => {
    setGameSettings((prev) => ({ ...prev, [key]: value }))
    setSuccessMessage(null)
  }

  const handleAccountSettingChange = (key: keyof typeof accountSettings, value: string) => {
    setAccountSettings((prev) => ({ ...prev, [key]: value }))
    setSuccessMessage(null)
  }

  const handleSaveGameSettings = async () => {
    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const updated = await settingsApi.update({ game: gameSettings })
      setSettings(updated)
      setSuccessMessage('Game settings saved successfully!')
    } catch (err: any) {
      console.error('Failed to save game settings:', err)
      setError(err.message || 'Failed to save settings. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleSaveAccountSettings = async () => {
    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const updated = await settingsApi.update({ general: accountSettings })
      setSettings(updated)
      setSuccessMessage('Account settings saved successfully!')
      
      // Update username in localStorage
      if (accountSettings.displayName && user) {
        const sessionData = localStorage.getItem('chessiq-session')
        if (sessionData) {
          const session = JSON.parse(sessionData)
          session.username = accountSettings.displayName
          localStorage.setItem('chessiq-session', JSON.stringify(session))
        }
      }
    } catch (err: any) {
      console.error('Failed to save account settings:', err)
      setError(err.message || 'Failed to save settings. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (passwordForm.newPassword !== confirmPassword) {
      setError('New password and confirmation do not match')
      return
    }
    
    if (passwordForm.newPassword.length < 6) {
      setError('New password must be at least 6 characters')
      return
    }

    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      await settingsApi.changePassword(passwordForm)
      setSuccessMessage('Password changed successfully!')
      setPasswordForm({ currentPassword: '', newPassword: '' })
      setConfirmPassword('')
    } catch (err: any) {
      console.error('Failed to change password:', err)
      setError(err.message || 'Failed to change password. Please check your current password.')
    } finally {
      setIsSaving(false)
    }
  }

  if (!user) return null

  return (
    <div className="settings-page">
      <Navbar />
      <main className="settings-main">
        <div className="settings-container">
          <header className="settings-header">
            <h1>Settings</h1>
            <p>Customize your ChessIQ experience</p>
          </header>

          {isLoading ? (
            <div className="settings-loading">
              <div className="spinner"></div>
              <p>Loading settings...</p>
            </div>
          ) : (
            <div className="settings-content">
              {/* Tabs */}
              <div className="settings-tabs">
                <button
                  className={`tab-button ${activeTab === 'game' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('game')
                    setError(null)
                    setSuccessMessage(null)
                  }}
                >
                  Game Settings
                </button>
                <button
                  className={`tab-button ${activeTab === 'account' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('account')
                    setError(null)
                    setSuccessMessage(null)
                  }}
                >
                  Account
                </button>
                <button
                  className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('security')
                    setError(null)
                    setSuccessMessage(null)
                  }}
                >
                  Security
                </button>
              </div>

              {/* Tab Content */}
              <div className="settings-card">
                {error && (
                  <div className="alert alert-error">
                    {error}
                  </div>
                )}
                
                {successMessage && (
                  <div className="alert alert-success">
                    {successMessage}
                  </div>
                )}

                {/* Game Settings Tab */}
                {activeTab === 'game' && (
                  <div className="tab-content">
                    <h2>Game Settings</h2>
                    <p className="tab-description">
                      Configure how the chess board behaves during gameplay
                    </p>

                    <div className="settings-section">
                      <div className="setting-item">
                        <div className="setting-info">
                          <label htmlFor="showLegalMoves">Show Legal Moves</label>
                          <p className="setting-description">
                            Highlight legal moves when a piece is selected
                          </p>
                        </div>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            id="showLegalMoves"
                            checked={gameSettings.showLegalMoves}
                            onChange={(e) => handleGameSettingChange('showLegalMoves', e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>

                      <div className="setting-item">
                        <div className="setting-info">
                          <label htmlFor="highlightLastMove">Highlight Last Move</label>
                          <p className="setting-description">
                            Highlight the last move made on the board
                          </p>
                        </div>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            id="highlightLastMove"
                            checked={gameSettings.highlightLastMove}
                            onChange={(e) => handleGameSettingChange('highlightLastMove', e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </label>
                      </div>
                    </div>

                    <div className="form-actions">
                      <button 
                        className="btn-primary"
                        onClick={handleSaveGameSettings}
                        disabled={isSaving}
                      >
                        {isSaving ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Account Settings Tab */}
                {activeTab === 'account' && (
                  <div className="tab-content">
                    <h2>Account Settings</h2>
                    <p className="tab-description">
                      Manage your account information and preferences
                    </p>

                    <div className="settings-section">
                      <div className="form-group">
                        <label htmlFor="displayName">Display Name</label>
                        <input
                          type="text"
                          id="displayName"
                          value={accountSettings.displayName}
                          onChange={(e) => handleAccountSettingChange('displayName', e.target.value)}
                          placeholder="Your display name"
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                          type="email"
                          id="email"
                          value={settings?.general.email || ''}
                          disabled
                        />
                        <span className="form-hint">Email cannot be changed</span>
                      </div>

                      <div className="form-group">
                        <label htmlFor="language">Language</label>
                        <select
                          id="language"
                          value={accountSettings.language}
                          onChange={(e) => handleAccountSettingChange('language', e.target.value)}
                        >
                          <option value="en">English</option>
                          <option value="es">Spanish</option>
                          <option value="fr">French</option>
                          <option value="de">German</option>
                          <option value="pt">Portuguese</option>
                          <option value="ru">Russian</option>
                          <option value="zh">Chinese</option>
                          <option value="ja">Japanese</option>
                          <option value="hi">Hindi</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="timezone">Timezone</label>
                        <select
                          id="timezone"
                          value={accountSettings.timezone}
                          onChange={(e) => handleAccountSettingChange('timezone', e.target.value)}
                        >
                          <option value="UTC">UTC</option>
                          <option value="America/New_York">Eastern Time (US)</option>
                          <option value="America/Chicago">Central Time (US)</option>
                          <option value="America/Denver">Mountain Time (US)</option>
                          <option value="America/Los_Angeles">Pacific Time (US)</option>
                          <option value="Europe/London">London</option>
                          <option value="Europe/Paris">Paris</option>
                          <option value="Asia/Tokyo">Tokyo</option>
                          <option value="Asia/Shanghai">Shanghai</option>
                          <option value="Asia/Kolkata">Kolkata</option>
                          <option value="Australia/Sydney">Sydney</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-actions">
                      <button 
                        className="btn-primary"
                        onClick={handleSaveAccountSettings}
                        disabled={isSaving}
                      >
                        {isSaving ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Security Tab */}
                {activeTab === 'security' && (
                  <div className="tab-content">
                    <h2>Security</h2>
                    <p className="tab-description">
                      Update your password to keep your account secure
                    </p>

                    <form onSubmit={handleChangePassword} className="settings-section">
                      <div className="form-group">
                        <label htmlFor="currentPassword">Current Password</label>
                        <input
                          type="password"
                          id="currentPassword"
                          value={passwordForm.currentPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                          placeholder="Enter your current password"
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="newPassword">New Password</label>
                        <input
                          type="password"
                          id="newPassword"
                          value={passwordForm.newPassword}
                          onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                          placeholder="Enter your new password"
                          required
                          minLength={6}
                        />
                        <span className="form-hint">Minimum 6 characters</span>
                      </div>

                      <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm New Password</label>
                        <input
                          type="password"
                          id="confirmPassword"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Confirm your new password"
                          required
                        />
                      </div>

                      <div className="form-actions">
                        <button 
                          type="submit"
                          className="btn-primary"
                          disabled={isSaving}
                        >
                          {isSaving ? 'Changing...' : 'Change Password'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default Settings
