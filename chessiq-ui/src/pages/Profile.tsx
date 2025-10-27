import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Navbar from '../components/navbar/Navbar'
import { profileApi, type UserProfile, type UpdateProfileData } from '../services/api'
import './profile.css'

function Profile() {
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  
  const [formData, setFormData] = useState<UpdateProfileData>({
    displayName: '',
    bio: '',
    country: '',
    timezone: 'UTC',
    language: 'en',
  })

  // Redirect if not logged in
  useEffect(() => {
    if (!user) {
      navigate('/signin')
    }
  }, [user, navigate])

  // Fetch profile data
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const data = await profileApi.get()
        setProfile(data)
        setFormData({
          displayName: data.username || '',
          bio: data.bio || '',
          country: data.country || '',
          timezone: data.timezone || 'UTC',
          language: data.language || 'en',
        })
      } catch (err) {
        console.error('Failed to fetch profile:', err)
        setError('Failed to load profile. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    if (user) {
      fetchProfile()
    }
  }, [user])

  const handleInputChange = (field: keyof UpdateProfileData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    setSuccessMessage(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const updatedProfile = await profileApi.update(formData)
      setProfile(updatedProfile)
      setSuccessMessage('Profile updated successfully!')
      
      // Update AuthContext username if changed
      if (formData.displayName && user) {
        const sessionData = localStorage.getItem('chessiq-session')
        if (sessionData) {
          const session = JSON.parse(sessionData)
          session.username = formData.displayName
          localStorage.setItem('chessiq-session', JSON.stringify(session))
        }
      }
    } catch (err: any) {
      console.error('Failed to update profile:', err)
      setError(err.message || 'Failed to update profile. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  if (!user) return null

  return (
    <div className="profile-page">
      <Navbar />
      <main className="profile-main">
        <div className="profile-container">
          <header className="profile-header">
            <h1>My Profile</h1>
            <p>Manage your personal information and preferences</p>
          </header>

          {isLoading ? (
            <div className="profile-loading">
              <div className="spinner"></div>
              <p>Loading profile...</p>
            </div>
          ) : (
            <div className="profile-content">
              {/* Profile Info Card */}
              <div className="profile-card profile-info-card">
                <h2>Account Information</h2>
                <div className="info-row">
                  <span className="info-label">Email:</span>
                  <span className="info-value">{profile?.email}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Role:</span>
                  <span className="info-value">{profile?.role}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Member Since:</span>
                  <span className="info-value">
                    {profile?.joinDate 
                      ? new Date(profile.joinDate).toLocaleDateString() 
                      : 'N/A'}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Last Active:</span>
                  <span className="info-value">
                    {profile?.lastActive 
                      ? new Date(profile.lastActive).toLocaleDateString() 
                      : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Edit Profile Form */}
              <div className="profile-card profile-edit-card">
                <h2>Edit Profile</h2>
                
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

                <form onSubmit={handleSubmit} className="profile-form">
                  <div className="form-group">
                    <label htmlFor="displayName">Display Name</label>
                    <input
                      type="text"
                      id="displayName"
                      value={formData.displayName}
                      onChange={(e) => handleInputChange('displayName', e.target.value)}
                      placeholder="Your display name"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="bio">Bio</label>
                    <textarea
                      id="bio"
                      value={formData.bio}
                      onChange={(e) => handleInputChange('bio', e.target.value)}
                      placeholder="Tell us about yourself..."
                      rows={4}
                    />
                    <span className="form-hint">
                      {formData.bio?.length || 0} / 500 characters
                    </span>
                  </div>

                  <div className="form-group">
                    <label htmlFor="country">Country</label>
                    <input
                      type="text"
                      id="country"
                      value={formData.country}
                      onChange={(e) => handleInputChange('country', e.target.value)}
                      placeholder="Your country"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="timezone">Timezone</label>
                    <select
                      id="timezone"
                      value={formData.timezone}
                      onChange={(e) => handleInputChange('timezone', e.target.value)}
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

                  <div className="form-group">
                    <label htmlFor="language">Language</label>
                    <select
                      id="language"
                      value={formData.language}
                      onChange={(e) => handleInputChange('language', e.target.value)}
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

                  <div className="form-actions">
                    <button 
                      type="submit" 
                      className="btn-primary"
                      disabled={isSaving}
                    >
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button 
                      type="button" 
                      className="btn-ghost"
                      onClick={() => navigate('/dashboard')}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default Profile
