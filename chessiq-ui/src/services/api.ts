// API Service for DeepChessIQ Backend Integration
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

/**
 * Generic API request helper with authentication
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get token from localStorage (must match SESSION_KEY in AuthContext)
  const sessionData = localStorage.getItem('chessiq-session')
  const user = sessionData ? JSON.parse(sessionData) : null
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(user?.token && { 'Authorization': `Bearer ${user.token}` }),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
  }

  return response.json()
}

// ==================== Profile API ====================

export interface UserProfile {
  id: string
  email: string
  username: string
  role: string
  bio: string | null
  avatarUrl: string | null
  country: string | null
  timezone: string
  language: string
  joinDate: string | null
  lastActive: string | null
}

export interface UpdateProfileData {
  displayName?: string
  bio?: string
  country?: string
  timezone?: string
  language?: string
}

export const profileApi = {
  /**
   * Get current user's profile
   */
  get: (): Promise<UserProfile> => {
    return apiRequest('/api/profile')
  },

  /**
   * Update current user's profile
   */
  update: (data: UpdateProfileData): Promise<UserProfile> => {
    return apiRequest('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },
}

// ==================== Settings API ====================

export interface GameSettings {
  showLegalMoves: boolean
  highlightLastMove: boolean
  boardTheme: string
  pieceSet: string
  autoQueen: boolean
  soundEnabled: boolean
}

export interface GeneralSettings {
  displayName: string
  email: string
  language: string
  timezone: string
}

export interface UserSettings {
  general: GeneralSettings
  game: GameSettings
}

export interface UpdateSettingsData {
  general?: Partial<GeneralSettings>
  game?: Partial<GameSettings>
}

export interface ChangePasswordData {
  currentPassword: string
  newPassword: string
}

export const settingsApi = {
  /**
   * Get user settings
   */
  get: (): Promise<UserSettings> => {
    return apiRequest('/api/settings')
  },

  /**
   * Update user settings
   */
  update: (data: UpdateSettingsData): Promise<UserSettings> => {
    return apiRequest('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  /**
   * Change user password
   */
  changePassword: (data: ChangePasswordData): Promise<{ message: string }> => {
    return apiRequest('/api/settings/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

// ==================== Games API ====================

export interface Game {
  id: string
  date: string
  opponent: string
  result: 'win' | 'loss' | 'draw'
  moves: number
  opening: string | null
  timeControl: string
  rating: number
  ratingChange: number
  duration: string
}

export interface GameDetails extends Game {
  userColor: string
  pgn: string | null
  fenFinal: string | null
}

export interface SaveGameData {
  result: 'win' | 'loss' | 'draw'
  userColor?: string
  totalMoves: number
  openingName?: string
  timeControl?: string
  ratingChange?: number
  durationSeconds?: number
  pgn?: string
  fenFinal?: string
}

export interface GameListParams {
  result?: 'win' | 'loss' | 'draw'
  limit?: number
  offset?: number
}

export const gamesApi = {
  /**
   * Get game history with optional filtering
   */
  list: (params?: GameListParams): Promise<{ games: Game[] }> => {
    const query = new URLSearchParams(params as any).toString()
    return apiRequest(`/api/games${query ? `?${query}` : ''}`)
  },

  /**
   * Get specific game details including PGN
   */
  get: (id: string): Promise<GameDetails> => {
    return apiRequest(`/api/games/${id}`)
  },

  /**
   * Save a new game
   */
  save: (data: SaveGameData): Promise<{ message: string; gameId: string; newRating: number }> => {
    return apiRequest('/api/games', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Delete a game
   */
  delete: (id: string): Promise<{ message: string }> => {
    return apiRequest(`/api/games/${id}`, {
      method: 'DELETE',
    })
  },
}

// ==================== Statistics API ====================

export interface UserStatistics {
  currentRating: number
  peakRating: number
  totalGamesPlayed: number
  wins: number
  losses: number
  draws: number
  winRatePercentage: number
  currentStreak: {
    type: 'win' | 'loss' | 'none'
    count: number
  }
  averageGameDuration: string
  gamesThisWeek: number
  lastGameDate: string | null
}

export interface RatingHistoryEntry {
  rating: number
  ratingChange: number
  date: string
}

export const statisticsApi = {
  /**
   * Get user statistics
   */
  get: (): Promise<UserStatistics> => {
    return apiRequest('/api/statistics')
  },

  /**
   * Get rating history for charts
   */
  ratingHistory: (limit = 30): Promise<{ history: RatingHistoryEntry[] }> => {
    return apiRequest(`/api/statistics/ratings/history?limit=${limit}`)
  },
}

