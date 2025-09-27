import Navbar from './Navbar'
import FeatureCard from './FeatureCard'
import './dashboard.css'

function Dashboard() {
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
            />
            <FeatureCard icon="▦" title="Analysis" description="Analyze games with human insights" />
            <FeatureCard icon="✸" title="Puzzles" description="Improve with training puzzles" />
            <FeatureCard
              icon="⚡"
              title="Hand & Brain"
              description="Play a collaborative variant with ChessIQ"
              accent
            />
            <FeatureCard icon="★" title="Openings" description="Learn and practice openings" />
            <FeatureCard
              icon="☯"
              title="Bot-or-Not"
              description="Distinguish between human and AI play"
            />
          </section>
        </div>
      </main>
    </div>
  )
}

export default Dashboard


