import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import AuthForm from '../components/auth/AuthForm'
import { Link } from 'react-router-dom'

function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const validatePassword = (password: string) => {
    return /[a-z]/.test(password) && /[A-Z]/.test(password) && /[0-9]/.test(password)
  }

  const validateForm = (form: any) => {
    if (!validatePassword(form.password)) {
      return 'Password must contain at least 1 uppercase letter, 1 lowercase letter, and 1 number.'
    }
    return null
  }

  const handleSubmit = async (form: any) => {
    const status = await register({
      username: form.username,
      email: form.email,
      password: form.password,
      role: form.role
    })
    if (status === 'ok') {
      navigate('/dashboard')
    }
    return status
  }

  return (
    <AuthForm
      title="Create your account"
      subtitle="Unlock insights tailored to the way humans play chess."
      pillText="Join ChessIQ"
      submitText="Register"
      loadingText="Creating…"
      footerText={
        <>
          Already have an account? <Link to="/signin">Sign in</Link>
        </>
      }
      onSubmit={handleSubmit}
      validateForm={validateForm}
    >
      <label className="auth-field">
        <span>Username</span>
        <input
          type="text"
          name="username"
          placeholder="chessmaster"
          minLength={3}
          required
        />
      </label>

      <label className="auth-field">
        <span>Email</span>
        <input
          type="email"
          name="email"
          placeholder="you@example.com"
          required
        />
      </label>

      <label className="auth-field">
        <span>Password</span>
        <input
          type="password"
          name="password"
          placeholder="••••••••"
          minLength={6}
          required
        />
        <small className="auth-hint">Min 6 characters, with upper, lower, and a digit.</small>
      </label>

      <label className="auth-field">
        <span>Role</span>
        <select name="role" defaultValue="user">
          <option value="user">User</option>
          <option value="coach">Coach</option>
          <option value="commentator">Commentator</option>
        </select>
      </label>
    </AuthForm>
  )
}

export default RegisterPage


