import Navbar from '../navbar/Navbar'
import FeatureCard from '../feature-card/FeatureCard'
import './dashboard.css'
import { useAuth } from '../../AuthContext'
import { useNavigate } from 'react-router-dom'

function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const isCoach = Boolean(user?.isCoach)
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
              <button className="btn-primary">Learn More</button>
              <button className="btn-ghost">Connect with Lichess</button>
            </div>
          </section>

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


