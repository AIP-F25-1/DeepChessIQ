import { useState } from 'react'
import './settings.css'

function GameSettings() {
  const [settings, setSettings] = useState({
    showLegalMoves: true,
    highlightLastMove: true,
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    // TODO: Save to backend API
    console.log('Saving game settings:', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="settings-section">
      <h2 className="settings-section-title">Game Settings</h2>
      <p className="settings-section-description">
        Configure your chess board and gameplay preferences
      </p>

      <div className="settings-form">
        <div className="settings-field">
          <label className="settings-checkbox">
            <input
              type="checkbox"
              checked={settings.showLegalMoves}
              onChange={(e) => setSettings({ ...settings, showLegalMoves: e.target.checked })}
            />
            <span>Show legal moves</span>
          </label>
          <p className="settings-field-hint">
            Highlight all legal moves when you select a piece
          </p>
        </div>

        <div className="settings-field">
          <label className="settings-checkbox">
            <input
              type="checkbox"
              checked={settings.highlightLastMove}
              onChange={(e) => setSettings({ ...settings, highlightLastMove: e.target.checked })}
            />
            <span>Highlight last move</span>
          </label>
          <p className="settings-field-hint">
            Show the previous move with a colored highlight
          </p>
        </div>

        <button className="btn-primary settings-save-btn" onClick={handleSave}>
          {saved ? '✓ Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}

export default GameSettings

