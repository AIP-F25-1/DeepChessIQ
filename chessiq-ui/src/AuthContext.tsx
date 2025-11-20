import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:3000'

export type UserRole = 'user' | 'coach' | 'commentator'

export type AuthUser = {
  id: number
  email: string
  role: UserRole
  token: string
  username:string
}

type Credentials = {
  email: string
  password: string
}

type Registration = Credentials & { username: string; role: UserRole }

type AuthContextValue = {
  user: AuthUser | null
  signIn: (form: Credentials) => Promise<'ok' | 'invalid' | 'error'>
  register: (form: Registration) => Promise<'ok' | 'exists' | 'error'>
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const SESSION_KEY = 'chessiq-session'

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(text || resp.statusText)
  }
  return resp.json() as Promise<T>
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return
    try {
      const parsed = JSON.parse(raw) as AuthUser
      setUser(parsed)
    } catch (error) {
      console.error('Failed to parse session', error)
      localStorage.removeItem(SESSION_KEY)
    }
  }, [])

  const signIn = async ({ email, password }: Credentials) => {
    try {
      const data = await postJSON<{ token: string; user: { id: number; email: string; role_code: UserRole ;display_name: string} }>(
        `${API_BASE}/auth/login`,
        { email, password },
      )
      const authUser: AuthUser = {
        id: data.user.id,
        email: data.user.email,
        role: data.user.role_code,
        token: data.token,
        username: data.user.display_name || data.user.email.split('@')[0],
      }
      setUser(authUser)
      localStorage.setItem(SESSION_KEY, JSON.stringify(authUser))
      return 'ok'
    } catch (error) {
      console.error('Sign in failed', error)
      if (error instanceof Error && /Invalid credentials/i.test(error.message)) {
        return 'invalid'
      }
      return 'error'
    }
  }

  const register = async ({ username, email, password, role }: Registration) => {
    try {
      const data = await postJSON<{ token: string; user: { id: number; email: string; role_code: UserRole ;display_name: string} }>(
        `${API_BASE}/auth/signup`,
        { email, password, role_code: role, displayName: username },
      )
      const authUser: AuthUser = {
        id: data.user.id,
        email: data.user.email,
        role: data.user.role_code,
        token: data.token,
        username: data.user.display_name || data.user.email.split('@')[0],
      }
      setUser(authUser)
      localStorage.setItem(SESSION_KEY, JSON.stringify(authUser))
      return 'ok'
    } catch (error) {
      console.error('Registration failed', error)
      if (error instanceof Error && /already registered/i.test(error.message)) {
        return 'exists'
      }
      return 'error'
    }
  }

  const signOut = () => {
    setUser(null)
    localStorage.removeItem(SESSION_KEY)
  }

  const value = useMemo(
    () => ({
      user,
      signIn,
      register,
      signOut,
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export { AuthProvider, useAuth }


