import { useState, useRef, useEffect } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../../AuthContext'
import { statisticsApi } from '../../services/api'
import './navbar.css'

function Navbar() {
  const { user, signOut } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [userRating, setUserRating] = useState<number | null>(null)

  // Fetch user rating
  useEffect(() => {
    const fetchRating = async () => {
      // Only fetch if user is logged in AND has a token
      if (!user || !user.token) return

      try {
        const stats = await statisticsApi.get()
        setUserRating(stats.currentRating)
      } catch (error) {
        // Silently fail - rating is optional
        console.debug('Could not fetch rating:', error)
      }
    }

    fetchRating()
  }, [user])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen)
  }

  const closeDropdown = () => {
    setDropdownOpen(false)
  }

  return (
    <header className="navbar">
      <div className="nav-left">
        <Link to="/" className="brand-link">
          <img src="/file.svg" alt="ChessIQ logo" className="nav-logo" />
          <span className="nav-brand">ChessIQ</span>
        </Link>
      </div>
      <nav className="nav-links">
        {user ? (
          <>
            <NavLink to="/">Play</NavLink>
            <NavLink to="/games">Games</NavLink>
            {user.role === 'coach' && (
              <NavLink to="/coach">Coach</NavLink>
            )}
          </>
        ) : (
          <>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/signin">Sign in</NavLink>
            <NavLink to="/register">Register</NavLink>
          </>
        )}
      </nav>
      <div className="nav-auth">
        {user ? (
          <div className="nav-user-menu" ref={dropdownRef}>
            <button 
              className="nav-user-button" 
              onClick={toggleDropdown}
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
            >
              {userRating !== null && (
                <span className="nav-user-rating">{userRating}</span>
              )}
              <span className="nav-user-name">{user.username}</span>
              <span className={`nav-dropdown-arrow ${dropdownOpen ? 'open' : ''}`}>▼</span>
            </button>
            
            {dropdownOpen && (
              <div className="nav-dropdown">
                <Link to="/profile" className="nav-dropdown-item" onClick={closeDropdown}>
                  <span className="nav-dropdown-icon">👤</span>
                  View Profile
                </Link>
                <Link to="/settings" className="nav-dropdown-item" onClick={closeDropdown}>
                  <span className="nav-dropdown-icon">⚙️</span>
                  Settings
                </Link>
                <div className="nav-dropdown-divider" />
                <button 
                  className="nav-dropdown-item nav-dropdown-signout" 
                  onClick={() => { signOut(); closeDropdown(); }}
                  type="button"
                >
                  <span className="nav-dropdown-icon">🚪</span>
                  Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link to="/signin" className="btn-ghost nav-signin">
            Sign in
          </Link>
        )}
      </div>
    </header>
  )
}

export default Navbar


