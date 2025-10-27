import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/navbar/Navbar'
import './game-library.css'

type GameRecord = {
  id: string
  date: string
  opponent: string
  result: 'win' | 'loss' | 'draw'
  moves: number
  opening: string
  timeControl: string
  rating: number
  ratingChange: number
}

// Static demo data
const demoGames: GameRecord[] = [
  {
    id: 'game-001',
    date: '2025-10-27',
    opponent: 'ChessIQ Bot',
    result: 'win',
    moves: 42,
    opening: 'Sicilian Defense',
    timeControl: '10+0',
    rating: 1520,
    ratingChange: 12,
  },
  {
    id: 'game-002',
    date: '2025-10-26',
    opponent: 'ChessIQ Bot',
    result: 'loss',
    moves: 38,
    opening: 'Italian Game',
    timeControl: '10+0',
    rating: 1508,
    ratingChange: -8,
  },
  {
    id: 'game-003',
    date: '2025-10-26',
    opponent: 'ChessIQ Bot',
    result: 'draw',
    moves: 56,
    opening: 'Queen\'s Gambit',
    timeControl: '10+0',
    rating: 1516,
    ratingChange: 0,
  },
  {
    id: 'game-004',
    date: '2025-10-25',
    opponent: 'ChessIQ Bot',
    result: 'win',
    moves: 35,
    opening: 'French Defense',
    timeControl: '10+0',
    rating: 1516,
    ratingChange: 10,
  },
  {
    id: 'game-005',
    date: '2025-10-24',
    opponent: 'ChessIQ Bot',
    result: 'loss',
    moves: 44,
    opening: 'Ruy Lopez',
    timeControl: '10+0',
    rating: 1506,
    ratingChange: -12,
  },
  {
    id: 'game-006',
    date: '2025-10-23',
    opponent: 'ChessIQ Bot',
    result: 'win',
    moves: 48,
    opening: 'King\'s Indian Defense',
    timeControl: '10+0',
    rating: 1518,
    ratingChange: 14,
  },
]

function GameLibrary() {
  const navigate = useNavigate()
  const [filterResult, setFilterResult] = useState<'all' | 'win' | 'loss' | 'draw'>('all')
  const [sortBy, setSortBy] = useState<'date' | 'rating' | 'moves'>('date')

  const filteredGames = useMemo(() => {
    let games = [...demoGames]

    // Filter by result
    if (filterResult !== 'all') {
      games = games.filter((game) => game.result === filterResult)
    }

    // Sort
    games.sort((a, b) => {
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

    return games
  }, [filterResult, sortBy])

  const stats = useMemo(() => {
    const wins = demoGames.filter((g) => g.result === 'win').length
    const losses = demoGames.filter((g) => g.result === 'loss').length
    const draws = demoGames.filter((g) => g.result === 'draw').length
    const winRate = demoGames.length > 0 ? ((wins / demoGames.length) * 100).toFixed(1) : '0.0'

    return { wins, losses, draws, winRate }
  }, [])

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

        {/* Stats Overview */}
        <section className="game-library-stats">
          <div className="stat-card">
            <div className="stat-label">Total Games</div>
            <div className="stat-value">{demoGames.length}</div>
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
      </main>
    </div>
  )
}

export default GameLibrary

