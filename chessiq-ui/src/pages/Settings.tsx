import { useState } from 'react'
import Navbar from '../components/navbar/Navbar'
import GeneralSettings from '../components/settings/GeneralSettings'
import GameSettings from '../components/settings/GameSettings'
import AccountSettings from '../components/settings/AccountSettings'
import '../styles/settings-page.css'

type SettingsTab = 'general' | 'game' | 'account'

function Settings() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  return (
    <div className="settings-page">
      <Navbar />
      <main className="settings-main">
        <div className="settings-container">
          <header className="settings-header">
            <h1>Settings</h1>
            <p>Manage your account preferences and game settings</p>
          </header>

          <div className="settings-layout">
            <aside className="settings-sidebar">
              <button
                className={`settings-tab ${activeTab === 'general' ? 'active' : ''}`}
                onClick={() => setActiveTab('general')}
              >
                <span className="settings-tab-icon">🌐</span>
                General
              </button>
              <button
                className={`settings-tab ${activeTab === 'game' ? 'active' : ''}`}
                onClick={() => setActiveTab('game')}
              >
                <span className="settings-tab-icon">♟️</span>
                Game
              </button>
              <button
                className={`settings-tab ${activeTab === 'account' ? 'active' : ''}`}
                onClick={() => setActiveTab('account')}
              >
                <span className="settings-tab-icon">🔒</span>
                Account
              </button>
            </aside>

            <div className="settings-content">
              {activeTab === 'general' && <GeneralSettings />}
              {activeTab === 'game' && <GameSettings />}
              {activeTab === 'account' && <AccountSettings />}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Settings

