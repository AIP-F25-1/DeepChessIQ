import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import Dashboard from './components/dashboard/Dashboard'
import HomePage from './pages/Home'
import RegisterPage from './pages/Register'
import SignInPage from './pages/SignIn'
import CoachDashboard from './pages/CoachDashboard'
import Settings from './pages/Settings'
import Profile from './pages/Profile'
import GameLibrary from './pages/GameLibrary'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signin" element={<SignInPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/coach" element={<CoachDashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/games" element={<GameLibrary />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
