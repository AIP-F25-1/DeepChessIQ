import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import '../styles/auth-page.css'

function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'user' as 'user' | 'coach' | 'commentator' })
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const validatePassword = (password: string) => {
    return /[a-z]/.test(password) && /[A-Z]/.test(password) && /[0-9]/.test(password)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!validatePassword(form.password)) {
      setError('Password must contain at least 1 uppercase letter, 1 lowercase letter, and 1 number.')
      return
    }

    setIsLoading(true)
    const status = await register(form)
    setIsLoading(false)

    if (status === 'ok') {
      navigate('/')
    } else if (status === 'exists') {
      setError('An account with this email already exists. Try signing in instead.')
    } else {
      setError('Unable to register with the provided details. Please review and try again.')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="auth-pill">Join ChessIQ</span>
          <h1>Create your account</h1>
          <p>Unlock insights tailored to the way humans play chess.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-field">
            <span>Username</span>
            <input
              type="text"
              value={form.username}
              onChange={(event) => setForm((prev) => ({ ...prev, username: event.target.value }))}
              placeholder="chessmaster"
              minLength={3}
              required
            />
          </label>

          <label className="auth-field">
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="you@example.com"
              required
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
              placeholder="••••••••"
              minLength={6}
              required
            />
            <small className="auth-hint">Min 6 characters, with upper, lower, and a digit.</small>
          </label>

          <label className="auth-field">
            <span>Role</span>
            <select
              value={form.role}
              onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value as 'user' | 'coach' | 'commentator' }))}
            >
              <option value="user">User</option>
              <option value="coach">Coach</option>
              <option value="commentator">Commentator</option>
            </select>
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn-primary auth-submit" disabled={isLoading}>
            {isLoading ? 'Creating…' : 'Register'}
          </button>
        </form>

        <div className="auth-divider">
          <span />
          <p>or</p>
          <span />
        </div>

        <button className="btn-ghost auth-google" type="button">
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" />
          Continue with Google
        </button>

        <p className="auth-footer">
          Already have an account? <Link to="/signin">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage


