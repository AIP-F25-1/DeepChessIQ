import { useState } from 'react'
import { useAuth } from '../../AuthContext'
import './basic-info.css'

function BasicInfo() {
  const { user } = useAuth()
  const [profile, setProfile] = useState({
    username: user?.username || '',
    displayName: user?.username || '',
    email: user?.email || '',
    bio: 'Chess enthusiast and lifelong learner',
    country: 'United States',
    avatarUrl: '',
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    // TODO: Save to backend API
    console.log('Saving profile:', profile)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // TODO: Upload to backend and get URL
      console.log('Uploading avatar:', file.name)
      const reader = new FileReader()
      reader.onloadend = () => {
        setProfile({ ...profile, avatarUrl: reader.result as string })
      }
      reader.readAsDataURL(file)
    }
  }

  return (
    <div className="basic-info-section">
      <h2 className="basic-info-title">Basic Information</h2>
      <p className="basic-info-description">
        Update your personal details and profile picture
      </p>

      <div className="basic-info-form">
        <div className="avatar-upload">
          <div className="avatar-preview">
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt="Avatar" />
            ) : (
              <div className="avatar-placeholder">
                {profile.username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          <div className="avatar-upload-controls">
            <label htmlFor="avatar-input" className="btn-primary">
              Upload Photo
            </label>
            <input
              id="avatar-input"
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              style={{ display: 'none' }}
            />
            <p className="avatar-hint">JPG, PNG or GIF. Max size 2MB.</p>
          </div>
        </div>

        <div className="basic-info-fields">
          <div className="basic-info-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={profile.username}
              onChange={(e) => setProfile({ ...profile, username: e.target.value })}
              className="basic-info-input"
            />
          </div>

          <div className="basic-info-field">
            <label htmlFor="display-name">Display Name</label>
            <input
              id="display-name"
              type="text"
              value={profile.displayName}
              onChange={(e) => setProfile({ ...profile, displayName: e.target.value })}
              className="basic-info-input"
            />
          </div>

          <div className="basic-info-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={profile.email}
              className="basic-info-input"
              disabled
            />
            <p className="basic-info-hint">Email cannot be changed</p>
          </div>

          <div className="basic-info-field">
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              value={profile.bio}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              className="basic-info-textarea"
              rows={4}
              maxLength={500}
            />
            <p className="basic-info-hint">{profile.bio.length}/500 characters</p>
          </div>

          <div className="basic-info-field">
            <label htmlFor="country">Country</label>
            <select
              id="country"
              value={profile.country}
              onChange={(e) => setProfile({ ...profile, country: e.target.value })}
              className="basic-info-select"
            >
              <option value="United States">United States</option>
              <option value="United Kingdom">United Kingdom</option>
              <option value="Canada">Canada</option>
              <option value="Australia">Australia</option>
              <option value="Germany">Germany</option>
              <option value="France">France</option>
              <option value="Spain">Spain</option>
              <option value="Italy">Italy</option>
              <option value="India">India</option>
              <option value="China">China</option>
              <option value="Japan">Japan</option>
              <option value="Brazil">Brazil</option>
              <option value="Mexico">Mexico</option>
              <option value="Russia">Russia</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <button className="btn-primary basic-info-save-btn" onClick={handleSave}>
            {saved ? '✓ Saved!' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default BasicInfo

