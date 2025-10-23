import './player-details-modal.css'

export type PlayerDetails = {
  id: string
  name: string
  email: string
  joinDate: string
  currentRating: number
  peakRating: number
  totalGamesPlayed: number
  wins: number
  losses: number
  draws: number
  winRatePercentage: number
  currentStreak: { type: 'win' | 'loss' | 'none'; count: number }
  averageGameDuration: string
  ratingChangeLast30Days: number
  gamesPlayedThisWeek: number
  lastCheckInDate: string
}

type PlayerDetailsModalProps = {
  player: PlayerDetails | null
  onClose: () => void
}

function PlayerDetailsModal({ player, onClose }: PlayerDetailsModalProps) {
  if (!player) return null

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <header className="modal-header">
          <div>
            <span className="modal-pill">Player Profile</span>
            <h2 className="modal-title">{player.name}</h2>
            <p className="modal-subtitle">{player.email}</p>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>

        <div className="modal-body">
          {/* Basic Information Section */}
          <section className="modal-section">
            <h3 className="modal-section-title">Basic Information</h3>
            <dl className="modal-grid">
              <div className="modal-stat">
                <dt>Join Date</dt>
                <dd>{player.joinDate}</dd>
              </div>
              <div className="modal-stat">
                <dt>Current Rating</dt>
                <dd className="stat-highlight">{player.currentRating}</dd>
              </div>
              <div className="modal-stat">
                <dt>Peak Rating</dt>
                <dd>{player.peakRating}</dd>
              </div>
              <div className="modal-stat">
                <dt>Rating Change (30d)</dt>
                <dd className={player.ratingChangeLast30Days >= 0 ? 'stat-positive' : 'stat-negative'}>
                  {player.ratingChangeLast30Days >= 0 ? '+' : ''}
                  {player.ratingChangeLast30Days}
                </dd>
              </div>
            </dl>
          </section>

          {/* Performance Statistics Section */}
          <section className="modal-section">
            <h3 className="modal-section-title">Performance Statistics</h3>
            <dl className="modal-grid">
              <div className="modal-stat">
                <dt>Total Games Played</dt>
                <dd>{player.totalGamesPlayed}</dd>
              </div>
              <div className="modal-stat">
                <dt>Win/Loss/Draw Record</dt>
                <dd>
                  {player.wins}W - {player.losses}L - {player.draws}D
                </dd>
              </div>
              <div className="modal-stat">
                <dt>Win Rate</dt>
                <dd className="stat-highlight">{player.winRatePercentage}%</dd>
              </div>
              <div className="modal-stat">
                <dt>Current Streak</dt>
                <dd>
                  {player.currentStreak.type === 'none'
                    ? 'No active streak'
                    : `${player.currentStreak.count} ${player.currentStreak.type}${player.currentStreak.count > 1 ? 's' : ''}`}
                </dd>
              </div>
              <div className="modal-stat">
                <dt>Avg Game Duration</dt>
                <dd>{player.averageGameDuration}</dd>
              </div>
            </dl>
          </section>

          {/* Activity Section */}
          <section className="modal-section">
            <h3 className="modal-section-title">Recent Activity</h3>
            <dl className="modal-grid">
              <div className="modal-stat">
                <dt>Games This Week</dt>
                <dd>{player.gamesPlayedThisWeek}</dd>
              </div>
              <div className="modal-stat">
                <dt>Last Check-in</dt>
                <dd>{player.lastCheckInDate}</dd>
              </div>
            </dl>
          </section>
        </div>

        <footer className="modal-footer">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Close
          </button>
          <button type="button" className="btn-primary">
            Send Message
          </button>
        </footer>
      </div>
    </div>
  )
}

export default PlayerDetailsModal

