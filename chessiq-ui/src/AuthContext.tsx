import { createContext, useContext, useEffect, useMemo, useState } from 'react'

type AuthUser = {
  username: string
  email: string
  isCoach?: boolean
}

type Credentials = {
  email: string
  password: string
}

type Registration = Credentials & { username: string }

type AuthContextValue = {
  user: AuthUser | null
  signIn: (form: Credentials) => Promise<'ok' | 'invalid'>
  register: (form: Registration) => Promise<'ok' | 'exists' | 'invalid'>
  signOut: () => void
  coachEmail: string
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const STORAGE_KEY = 'chessiq-users'
const SESSION_KEY = 'chessiq-session'
// Coach/admin config via env (Vite). Fallbacks keep dev experience working.
const env = (import.meta as any).env ?? {}
const COACH_EMAIL = (env.VITE_COACH_EMAIL as string) || 'coach@chessiq.com'
const COACH_PASSWORD = (env.VITE_COACH_PASSWORD as string) || 'Coach123'
const COACH_USERNAME = (env.VITE_COACH_USERNAME as string) || 'Coach Master'
const SEED_COACH = String(env.VITE_SEED_COACH || 'true') === 'true'

function readUsers(): Registration[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Registration[]) : []
  } catch (error) {
    console.error('Failed to parse users from storage', error)
    return []
  }
}

function writeUsers(users: Registration[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users))
}

function ensureCoachSeed() {
  localStorage.setItem('coach-email', COACH_EMAIL)
  if (!SEED_COACH) return
  const users = readUsers()
  const coachExists = users.some((entry) => entry.email === COACH_EMAIL)
  if (coachExists) return

  const seeded = [...users, { username: COACH_USERNAME, email: COACH_EMAIL, password: COACH_PASSWORD }]
  writeUsers(seeded)
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    ensureCoachSeed()
    const raw = localStorage.getItem(SESSION_KEY)
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as AuthUser
        setUser(parsed)
      } catch (error) {
        console.error('Failed to parse session', error)
        localStorage.removeItem(SESSION_KEY)
      }
    }
  }, [])

  const signIn = async ({ email, password }: Credentials) => {
    ensureCoachSeed()
    const users = readUsers()
    const match = users.find((entry) => entry.email === email && entry.password === password)
    if (!match) return 'invalid'

    const authUser: AuthUser = {
      username: match.username,
      email: match.email,
      isCoach: match.email === COACH_EMAIL,
    }
    setUser(authUser)
    localStorage.setItem(SESSION_KEY, JSON.stringify(authUser))
    return 'ok'
  }

  const register = async ({ username, email, password }: Registration) => {
    const users = readUsers()
    const exists = users.some((entry) => entry.email === email)
    if (exists) return 'exists'

    if (email === COACH_EMAIL) {
      return 'exists'
    }

    // password constraints already validated by form, but keep minimal guard
    if (!/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
      return 'invalid'
    }

    const newUsers = [...users, { username, email, password }]
    writeUsers(newUsers)

    const authUser: AuthUser = { username, email, isCoach: email === COACH_EMAIL }
    setUser(authUser)
    localStorage.setItem(SESSION_KEY, JSON.stringify(authUser))
    return 'ok'
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
      coachEmail: localStorage.getItem('coach-email') ?? COACH_EMAIL,
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


