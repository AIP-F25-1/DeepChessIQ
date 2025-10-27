import Navbar from '../components/navbar/Navbar'
import BasicInfo from '../components/profile/BasicInfo'
import Statistics from '../components/profile/Statistics'
import '../styles/profile.css'

function Profile() {
  return (
    <div className="profile-page">
      <Navbar />
      <main className="profile-main">
        <div className="profile-container">
          <header className="profile-header">
            <h1>My Profile</h1>
            <p>Manage your personal information and view your statistics</p>
          </header>

          <div className="profile-content">
            <BasicInfo />
            <Statistics />
          </div>
        </div>
      </main>
    </div>
  )
}

export default Profile

