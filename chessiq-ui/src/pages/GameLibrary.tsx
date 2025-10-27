import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import Navbar from '../components/navbar/Navbar'
import { gamesApi, type Game } from '../services/api'
import './game-library.css'

function GameLibrary() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [games, setGames] = useState<Game[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterResult, setFilterResult] = useState<'all' | 'win' | 'loss' | 'draw'>('all')
  const [sortBy, setSortBy] = useState<'date' | 'rating' | 'moves'>('date')

  // Redirect if not logged in
  useEffect(() => {
    if (!user) {
      navigate('/signin')
    }
  }, [user, navigate])

  // Fetch games from API
  useEffect(() => {
    const fetchGames = async () => {
      if (!user) return

      try {
        setIsLoading(true)
        setError(null)
        const response = await gamesApi.list({ limit: 100 })
        setGames(response.games)
      } catch (err: any) {
        console.error('Failed to fetch games:', err)
        setError('Failed to load games. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchGames()
  }, [user])

  const filteredGames = useMemo(() => {
    let filteredList = [...games]

    // Filter by result
    if (filterResult !== 'all') {
      filteredList = filteredList.filter((game) => game.result === filterResult)
    }

    // Sort
    filteredList.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.date).getTime() - new Date(a.date).getTime()
      }
      if (sortBy === 'rating') {
        return b.rating - a.rating
      }
      if (sortBy === 'moves') {
        return b.moves - a.moves
      }
      return 0
    })

    return filteredList
  }, [games, filterResult, sortBy])

  const stats = useMemo(() => {
    const wins = games.filter((g) => g.result === 'win').length
    const losses = games.filter((g) => g.result === 'loss').length
    const draws = games.filter((g) => g.result === 'draw').length
    const winRate = games.length > 0 ? ((wins / games.length) * 100).toFixed(1) : '0.0'

    return { wins, losses, draws, winRate }
  }, [games])

  const getResultIcon = (result: string) => {
    if (result === 'win') return '✓'
    if (result === 'loss') return '✗'
    return '='
  }

  const getResultClass = (result: string) => {
    if (result === 'win') return 'game-result-win'
    if (result === 'loss') return 'game-result-loss'
    return 'game-result-draw'
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  if (!user) return null

  return (
    <div className="game-library">
      <Navbar />
      <main className="game-library-main">
        <header className="game-library-header">
          <div>
            <h1 className="game-library-title">Game Library</h1>
            <p className="game-library-subtitle">Review your past games and track your progress</p>
          </div>
        </header>

        {isLoading ? (
          <div className="game-library-loading">
            <div className="spinner"></div>
            <p>Loading games...</p>
          </div>
        ) : error ? (
          <div className="game-library-error">
            <p>{error}</p>
            <button className="btn-primary" onClick={() => window.location.reload()}>
              Retry
            </button>
          </div>
        ) : (
          <>
            {/* Stats Overview */}
            <section className="game-library-stats">
              <div className="stat-card">
                <div className="stat-label">Total Games</div>
                <div className="stat-value">{games.length}</div>
              </div>
          <div className="stat-card stat-card-win">
            <div className="stat-label">Wins</div>
            <div className="stat-value">{stats.wins}</div>
          </div>
          <div className="stat-card stat-card-loss">
            <div className="stat-label">Losses</div>
            <div className="stat-value">{stats.losses}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Draws</div>
            <div className="stat-value">{stats.draws}</div>
          </div>
          <div className="stat-card stat-card-highlight">
            <div className="stat-label">Win Rate</div>
            <div className="stat-value">{stats.winRate}%</div>
          </div>
        </section>

        {/* Filters and Sort */}
        <section className="game-library-controls">
          <div className="game-library-filters">
            <button
              className={`filter-btn ${filterResult === 'all' ? 'active' : ''}`}
              onClick={() => setFilterResult('all')}
            >
              All Games
            </button>
            <button
              className={`filter-btn ${filterResult === 'win' ? 'active' : ''}`}
              onClick={() => setFilterResult('win')}
            >
              Wins
            </button>
            <button
              className={`filter-btn ${filterResult === 'loss' ? 'active' : ''}`}
              onClick={() => setFilterResult('loss')}
            >
              Losses
            </button>
            <button
              className={`filter-btn ${filterResult === 'draw' ? 'active' : ''}`}
              onClick={() => setFilterResult('draw')}
            >
              Draws
            </button>
          </div>

          <div className="game-library-sort">
            <label htmlFor="sort-select">Sort by:</label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'date' | 'rating' | 'moves')}
            >
              <option value="date">Date</option>
              <option value="rating">Rating</option>
              <option value="moves">Moves</option>
            </select>
          </div>
        </section>

        {/* Games List */}
        <section className="game-library-list">
          {filteredGames.length === 0 ? (
            <div className="no-games">
              <p>No games found</p>
              <button className="btn-primary" onClick={() => navigate('/')}>
                Play a Game
              </button>
            </div>
          ) : (
            filteredGames.map((game) => (
              <article key={game.id} className="game-card">
                <div className="game-card-header">
                  <div className={`game-result ${getResultClass(game.result)}`}>
                    <span className="game-result-icon">{getResultIcon(game.result)}</span>
                    <span className="game-result-text">{game.result.toUpperCase()}</span>
                  </div>
                  <div className="game-date">{formatDate(game.date)}</div>
                </div>

                <div className="game-card-body">
                  <div className="game-info-row">
                    <span className="game-info-label">Opponent:</span>
                    <span className="game-info-value">{game.opponent}</span>
                  </div>
                  <div className="game-info-row">
                    <span className="game-info-label">Opening:</span>
                    <span className="game-info-value">{game.opening}</span>
                  </div>
                  <div className="game-info-row">
                    <span className="game-info-label">Moves:</span>
                    <span className="game-info-value">{game.moves}</span>
                  </div>
                  <div className="game-info-row">
                    <span className="game-info-label">Time Control:</span>
                    <span className="game-info-value">{game.timeControl}</span>
                  </div>
                  <div className="game-info-row">
                    <span className="game-info-label">Rating:</span>
                    <span className="game-info-value">
                      {game.rating}{' '}
                      <span className={game.ratingChange >= 0 ? 'rating-up' : 'rating-down'}>
                        ({game.ratingChange >= 0 ? '+' : ''}{game.ratingChange})
                      </span>
                    </span>
                  </div>
                </div>

                <div className="game-card-footer">
                  <button className="btn-ghost" onClick={() => console.log('View game:', game.id)}>
                    View Game
                  </button>
                  <button className="btn-ghost" onClick={() => console.log('Analyze game:', game.id)}>
                    Analyze
                  </button>
                </div>
              </article>
            ))
          )}
        </section>
          </>
        )}
      </main>
    </div>
  )
}

export default GameLibrary

