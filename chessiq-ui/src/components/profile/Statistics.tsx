import './statistics.css'

function Statistics() {
  // Static data - will be replaced with API call
  const stats = {
    totalGames: 127,
    wins: 68,
    losses: 45,
    draws: 14,
    winRate: 53.5,
    currentRating: 1420,
    peakRating: 1485,
    ratingHistory: [
      { date: '2025-01-15', rating: 1350 },
      { date: '2025-02-01', rating: 1385 },
      { date: '2025-03-01', rating: 1410 },
      { date: '2025-04-01', rating: 1435 },
      { date: '2025-05-01', rating: 1465 },
      { date: '2025-06-01', rating: 1485 },
      { date: '2025-07-01', rating: 1470 },
      { date: '2025-08-01', rating: 1455 },
      { date: '2025-09-01', rating: 1440 },
      { date: '2025-10-01', rating: 1420 },
    ],
  }

  const winPercentage = (stats.wins / stats.totalGames) * 100
  const lossPercentage = (stats.losses / stats.totalGames) * 100
  const drawPercentage = (stats.draws / stats.totalGames) * 100

  return (
    <div className="statistics-section">
      <h2 className="statistics-title">Statistics</h2>
      <p className="statistics-description">
        Your performance overview and rating progression
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Total Games</span>
          <span className="stat-value">{stats.totalGames}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Win Rate</span>
          <span className="stat-value stat-highlight">{stats.winRate}%</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Current Rating</span>
          <span className="stat-value stat-highlight">{stats.currentRating}</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Peak Rating</span>
          <span className="stat-value">{stats.peakRating}</span>
        </div>
      </div>

      <div className="rating-chart-container">
        <h3 className="rating-chart-title">Rating History</h3>
        <div className="rating-chart">
          <svg viewBox="0 0 800 300" className="rating-chart-svg">
            {/* Grid lines */}
            <line x1="50" y1="250" x2="750" y2="250" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            <line x1="50" y1="200" x2="750" y2="200" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            <line x1="50" y1="150" x2="750" y2="150" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            <line x1="50" y1="100" x2="750" y2="100" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            <line x1="50" y1="50" x2="750" y2="50" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />

            {/* Y-axis labels */}
            <text x="30" y="255" fill="rgba(255,255,255,0.5)" fontSize="12">1300</text>
            <text x="30" y="205" fill="rgba(255,255,255,0.5)" fontSize="12">1350</text>
            <text x="30" y="155" fill="rgba(255,255,255,0.5)" fontSize="12">1400</text>
            <text x="30" y="105" fill="rgba(255,255,255,0.5)" fontSize="12">1450</text>
            <text x="30" y="55" fill="rgba(255,255,255,0.5)" fontSize="12">1500</text>

            {/* Rating line */}
            <polyline
              points={stats.ratingHistory
                .map((point, index) => {
                  const x = 50 + (index * 700) / (stats.ratingHistory.length - 1)
                  const y = 250 - ((point.rating - 1300) / 200) * 200
                  return `${x},${y}`
                })
                .join(' ')}
              fill="none"
              stroke="url(#ratingGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data points */}
            {stats.ratingHistory.map((point, index) => {
              const x = 50 + (index * 700) / (stats.ratingHistory.length - 1)
              const y = 250 - ((point.rating - 1300) / 200) * 200
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="4"
                  fill="#8b5cf6"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
              )
            })}

            {/* Gradient definition */}
            <defs>
              <linearGradient id="ratingGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="100%" stopColor="#6d28d9" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <div className="record-breakdown">
        <h3 className="record-breakdown-title">Game Record</h3>
        <div className="record-bars">
          <div className="record-bar-container">
            <div className="record-bar bar-wins" style={{ width: `${winPercentage}%` }}>
              <span className="record-bar-label">{stats.wins}W</span>
            </div>
          </div>
          <div className="record-bar-container">
            <div className="record-bar bar-losses" style={{ width: `${lossPercentage}%` }}>
              <span className="record-bar-label">{stats.losses}L</span>
            </div>
          </div>
          <div className="record-bar-container">
            <div className="record-bar bar-draws" style={{ width: `${drawPercentage}%` }}>
              <span className="record-bar-label">{stats.draws}D</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Statistics

