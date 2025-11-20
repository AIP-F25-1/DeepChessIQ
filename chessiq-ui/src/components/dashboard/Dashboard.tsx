import { useEffect, useState } from 'react'
import Navbar from '../navbar/Navbar'
import FeatureCard from '../feature-card/FeatureCard'
import './dashboard.css'
import { useAuth } from '../../AuthContext'
import { useNavigate } from 'react-router-dom'
import { statisticsApi, type UserStatistics } from '../../services/api'

function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isCoach = user?.role === 'coach'
  const [stats, setStats] = useState<UserStatistics | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)

  // Fetch user statistics
  useEffect(() => {
    const fetchStats = async () => {
      // Only fetch if user is logged in AND has a token
      if (!user || !user.token) {
        setIsLoadingStats(false)
        return
      }

      try {
        setIsLoadingStats(true)
        const data = await statisticsApi.get()
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch statistics:', error)
      } finally {
        setIsLoadingStats(false)
      }
    }

    fetchStats()
  }, [user])

  return (
    <div className="dashboard">
      <Navbar />
      <main className="dash-main">
        <div className="dash-layout">
          <section className="dash-hero">
            <span className="dash-pretitle">Human-style Chess Engine</span>
            <h1 className="dash-title">The human chess AI</h1>
            <p className="dash-subtitle">
              ChessIQ is a neural network chess model that captures human style. Enjoy realistic
              games, insightful analysis, and a new way of seeing chess.
            </p>
            <div className="dash-cta">
              <button className="btn-primary" onClick={() => navigate('/')}>
                Play Now
              </button>
              <button className="btn-ghost" onClick={() => navigate('/games')}>
                View Game Library
              </button>
            </div>
          </section>

          {/* Statistics Section */}
          {user && (
            <section className="dash-stats">
              <h2 className="dash-stats-title">Your Statistics</h2>
              {isLoadingStats ? (
                <div className="dash-stats-loading">
                  <div className="spinner"></div>
                </div>
              ) : stats ? (
                <div className="dash-stats-grid">
                  <div className="stat-box">
                    <div className="stat-label">Rating</div>
                    <div className="stat-value">{stats.currentRating}</div>
                    <div className="stat-sublabel">Peak: {stats.peakRating}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Total Games</div>
                    <div className="stat-value">{stats.totalGamesPlayed}</div>
                    <div className="stat-sublabel">{stats.gamesThisWeek} this week</div>
                  </div>
                  <div className="stat-box stat-box-win">
                    <div className="stat-label">Wins</div>
                    <div className="stat-value">{stats.wins}</div>
                    <div className="stat-sublabel">{stats.winRatePercentage}% win rate</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Losses</div>
                    <div className="stat-value">{stats.losses}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Draws</div>
                    <div className="stat-value">{stats.draws}</div>
                  </div>
                  <div className="stat-box stat-box-highlight">
                    <div className="stat-label">Current Streak</div>
                    <div className="stat-value">
                      {stats.currentStreak.type === 'none' 
                        ? '—' 
                        : `${stats.currentStreak.count} ${stats.currentStreak.type}`}
                    </div>
                    <div className="stat-sublabel">Avg: {stats.averageGameDuration}</div>
                  </div>
                </div>
              ) : null}
            </section>
          )}

          <section className="dash-grid">
            <FeatureCard
              icon="♞"
              title="Play ChessIQ"
              description="Play chess against the human-like ChessIQ engine"
              onClick={() => navigate('/')}
            />
            <FeatureCard icon="▦" title="Analysis" description="Analyze games with human insights" />
            {isCoach && (
              <FeatureCard
                icon="🎓"
                title="Coach tools"
                description="Manage students, review progress, and assign plans"
                accent
                onClick={() => navigate('/coach')}
              />
            )}
          </section>
        </div>
      </main>
    </div>
  )
}

export default Dashboard


