import { useState } from 'react'
import './settings.css'

function GeneralSettings() {
  const [settings, setSettings] = useState({
    language: 'en',
    timezone: 'UTC-5',
    theme: 'dark' as 'light' | 'dark' | 'auto',
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    // TODO: Save to backend API
    console.log('Saving general settings:', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="settings-section">
      <h2 className="settings-section-title">General Settings</h2>
      <p className="settings-section-description">
        Customize your language, timezone, and appearance preferences
      </p>

      <div className="settings-form">
        <div className="settings-field">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            value={settings.language}
            onChange={(e) => setSettings({ ...settings, language: e.target.value })}
            className="settings-select"
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
            <option value="pt">Portuguese</option>
          </select>
        </div>

        <div className="settings-field">
          <label htmlFor="timezone">Timezone</label>
          <select
            id="timezone"
            value={settings.timezone}
            onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
            className="settings-select"
          >
            <option value="UTC-12">UTC-12:00 (Baker Island)</option>
            <option value="UTC-11">UTC-11:00 (American Samoa)</option>
            <option value="UTC-10">UTC-10:00 (Hawaii)</option>
            <option value="UTC-9">UTC-09:00 (Alaska)</option>
            <option value="UTC-8">UTC-08:00 (Pacific Time)</option>
            <option value="UTC-7">UTC-07:00 (Mountain Time)</option>
            <option value="UTC-6">UTC-06:00 (Central Time)</option>
            <option value="UTC-5">UTC-05:00 (Eastern Time)</option>
            <option value="UTC-4">UTC-04:00 (Atlantic Time)</option>
            <option value="UTC-3">UTC-03:00 (Buenos Aires)</option>
            <option value="UTC-2">UTC-02:00 (Mid-Atlantic)</option>
            <option value="UTC-1">UTC-01:00 (Azores)</option>
            <option value="UTC+0">UTC+00:00 (London)</option>
            <option value="UTC+1">UTC+01:00 (Paris)</option>
            <option value="UTC+2">UTC+02:00 (Cairo)</option>
            <option value="UTC+3">UTC+03:00 (Moscow)</option>
            <option value="UTC+4">UTC+04:00 (Dubai)</option>
            <option value="UTC+5">UTC+05:00 (Karachi)</option>
            <option value="UTC+5.5">UTC+05:30 (Mumbai)</option>
            <option value="UTC+6">UTC+06:00 (Dhaka)</option>
            <option value="UTC+7">UTC+07:00 (Bangkok)</option>
            <option value="UTC+8">UTC+08:00 (Singapore)</option>
            <option value="UTC+9">UTC+09:00 (Tokyo)</option>
            <option value="UTC+10">UTC+10:00 (Sydney)</option>
            <option value="UTC+11">UTC+11:00 (Solomon Islands)</option>
            <option value="UTC+12">UTC+12:00 (Auckland)</option>
          </select>
        </div>

        <div className="settings-field">
          <label>Theme</label>
          <div className="settings-radio-group">
            <label className="settings-radio">
              <input
                type="radio"
                name="theme"
                value="light"
                checked={settings.theme === 'light'}
                onChange={(e) => setSettings({ ...settings, theme: e.target.value as 'light' | 'dark' | 'auto' })}
              />
              <span>Light</span>
            </label>
            <label className="settings-radio">
              <input
                type="radio"
                name="theme"
                value="dark"
                checked={settings.theme === 'dark'}
                onChange={(e) => setSettings({ ...settings, theme: e.target.value as 'light' | 'dark' | 'auto' })}
              />
              <span>Dark</span>
            </label>
            <label className="settings-radio">
              <input
                type="radio"
                name="theme"
                value="auto"
                checked={settings.theme === 'auto'}
                onChange={(e) => setSettings({ ...settings, theme: e.target.value as 'light' | 'dark' | 'auto' })}
              />
              <span>Auto</span>
            </label>
          </div>
        </div>

        <button className="btn-primary settings-save-btn" onClick={handleSave}>
          {saved ? '✓ Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}

export default GeneralSettings

