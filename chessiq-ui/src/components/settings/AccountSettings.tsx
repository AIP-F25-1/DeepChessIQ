import { useState } from 'react'
import './settings.css'

function AccountSettings() {
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [deleteConfirmation, setDeleteConfirmation] = useState('')

  const handleChangePassword = () => {
    // TODO: Call API to change password
    console.log('Changing password')
    setShowPasswordModal(false)
    setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
  }

  const handleDeleteAccount = () => {
    // TODO: Call API to delete account
    console.log('Deleting account')
    setShowDeleteModal(false)
  }

  return (
    <div className="settings-section">
      <h2 className="settings-section-title">Account Settings</h2>
      <p className="settings-section-description">
        Manage your account security and preferences
      </p>

      <div className="settings-form">
        <div className="settings-action-group">
          <div>
            <h3 className="settings-action-title">Change Password</h3>
            <p className="settings-action-description">
              Update your password to keep your account secure
            </p>
          </div>
          <button className="btn-primary" onClick={() => setShowPasswordModal(true)}>
            Change Password
          </button>
        </div>

        <div className="settings-divider" />

        <div className="settings-action-group">
          <div>
            <h3 className="settings-action-title settings-danger">Delete Account</h3>
            <p className="settings-action-description">
              Permanently delete your account and all associated data
            </p>
          </div>
          <button className="btn-danger" onClick={() => setShowDeleteModal(true)}>
            Delete Account
          </button>
        </div>
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="settings-modal-backdrop" onClick={() => setShowPasswordModal(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Change Password</h3>
            <div className="settings-modal-form">
              <div className="settings-field">
                <label htmlFor="current-password">Current Password</label>
                <input
                  type="password"
                  id="current-password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                  className="settings-input"
                />
              </div>
              <div className="settings-field">
                <label htmlFor="new-password">New Password</label>
                <input
                  type="password"
                  id="new-password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                  className="settings-input"
                />
              </div>
              <div className="settings-field">
                <label htmlFor="confirm-password">Confirm New Password</label>
                <input
                  type="password"
                  id="confirm-password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  className="settings-input"
                />
              </div>
            </div>
            <div className="settings-modal-actions">
              <button className="btn-ghost" onClick={() => setShowPasswordModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleChangePassword}>
                Change Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="settings-modal-backdrop" onClick={() => setShowDeleteModal(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="settings-danger">Delete Account</h3>
            <p className="settings-modal-warning">
              ⚠️ This action cannot be undone. All your games, statistics, and data will be permanently deleted.
            </p>
            <div className="settings-modal-form">
              <div className="settings-field">
                <label htmlFor="delete-confirmation">
                  Type <strong>DELETE</strong> to confirm
                </label>
                <input
                  type="text"
                  id="delete-confirmation"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="settings-input"
                  placeholder="DELETE"
                />
              </div>
            </div>
            <div className="settings-modal-actions">
              <button className="btn-ghost" onClick={() => setShowDeleteModal(false)}>
                Cancel
              </button>
              <button
                className="btn-danger"
                onClick={handleDeleteAccount}
                disabled={deleteConfirmation !== 'DELETE'}
              >
                Delete Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountSettings

