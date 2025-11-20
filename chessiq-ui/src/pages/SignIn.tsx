import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import AuthForm from '../components/auth/AuthForm'
import { Link } from 'react-router-dom'

function SignInPage() {
  const navigate = useNavigate()
  const { signIn } = useAuth()

  const handleSubmit = async (form: any) => {
    const status = await signIn({ email: form.email, password: form.password })
    if (status === 'ok') {
      navigate('/dashboard')
    }
    return status
  }

  return (
    <AuthForm
      title="Sign in to ChessIQ"
      subtitle="Continue exploring human-style chess insights."
      pillText="Welcome back"
      submitText="Sign In"
      loadingText="Signing in…"
      footerText={
        <>
          Don't have an account? <Link to="/register">Create one</Link>
        </>
      }
      onSubmit={handleSubmit}
    >
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
      </label>
    </AuthForm>
  )
}

export default SignInPage


