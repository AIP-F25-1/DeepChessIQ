import { createContext, useContext, useEffect, useMemo, useState } from 'react'

type AuthUser = {
  username: string
  email: string
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
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const STORAGE_KEY = 'chessiq-users'
const SESSION_KEY = 'chessiq-session'

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

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
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
    const users = readUsers()
    const match = users.find((entry) => entry.email === email && entry.password === password)
    if (!match) return 'invalid'

    const authUser: AuthUser = { username: match.username, email: match.email }
    setUser(authUser)
    localStorage.setItem(SESSION_KEY, JSON.stringify(authUser))
    return 'ok'
  }

  const register = async ({ username, email, password }: Registration) => {
    const users = readUsers()
    const exists = users.some((entry) => entry.email === email)
    if (exists) return 'exists'

    // password constraints already validated by form, but keep minimal guard
    if (!/[a-z]/.test(password) || !/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
      return 'invalid'
    }

    const newUsers = [...users, { username, email, password }]
    writeUsers(newUsers)

    const authUser: AuthUser = { username, email }
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


