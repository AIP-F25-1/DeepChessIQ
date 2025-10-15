import { type FormEvent, useState, type ReactNode } from 'react'
import '../../styles/auth-page.css'

type AuthFormProps = {
  title: string
  subtitle: string
  pillText: string
  submitText: string
  loadingText: string
  footerText: ReactNode
  onSubmit: (form: any) => Promise<string>
  validateForm?: (form: any) => string | null
  children: ReactNode
}

function AuthForm({
  title,
  subtitle,
  pillText,
  submitText,
  loadingText,
  footerText,
  onSubmit,
  validateForm,
  children
}: Readonly<AuthFormProps>) {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    const formData = new FormData(event.currentTarget)
    const form = Object.fromEntries(formData.entries())

    if (validateForm) {
      const validationError = validateForm(form)
      if (validationError) {
        setError(validationError)
        return
      }
    }

    setIsLoading(true)
    const status = await onSubmit(form)
    setIsLoading(false)

    if (status === 'ok') {
      // Navigation handled by parent
    } else if (status === 'invalid') {
      setError('Invalid credentials. Please try again.')
    } else if (status === 'exists') {
      setError('An account with this email already exists. Try signing in instead.')
    } else {
      setError('Unable to process your request. Please try again later.')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="auth-pill">{pillText}</span>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {children}

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="btn-primary auth-submit" disabled={isLoading}>
            {isLoading ? loadingText : submitText}
          </button>
        </form>

        <div className="auth-divider">
          <span />
          <p>or</p>
          <span />
        </div>

        <button className="btn-ghost auth-google" type="button" disabled>
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" />
          <span>Continue with Google (coming soon)</span>
        </button>

        <p className="auth-footer">
          {footerText}
        </p>
      </div>
    </div>
  )
}

export default AuthForm
