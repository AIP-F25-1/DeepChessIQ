import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import './navbar.css'

function Navbar() {
  const { user, signOut } = useAuth()

  return (
    <header className="navbar">
      <div className="nav-left">
        <Link to="/" className="brand-link">
          <img src="/file.svg" alt="ChessIQ logo" className="nav-logo" />
          <span className="nav-brand">ChessIQ</span>
        </Link>
      </div>
      <nav className="nav-links">
        <NavLink to="/dashboard">
          Dashboard
        </NavLink>
        <NavLink to="/signin">Sign in</NavLink>
        <NavLink to="/register">Register</NavLink>
      </nav>
      <div className="nav-auth">
        {user ? (
          <>
            <span className="nav-user">{user.username}</span>
            <button className="btn-ghost" onClick={signOut} type="button">
              Sign out
            </button>
          </>
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


