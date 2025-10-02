import './commentary.css'
import { useEffect, useRef } from 'react'

type CommentaryProps = {
  moveHistory: string[]
  currentTurn: 'w' | 'b'
  inCheck: boolean
  gameOver: boolean
}

function Commentary({ moveHistory, currentTurn, inCheck, gameOver }: CommentaryProps) {
  const movesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new moves are added
  useEffect(() => {
    movesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [moveHistory])

  const formatMoveNumber = (index: number) => {
    return Math.ceil((index + 1) / 2)
  }

  const isWhiteMove = (index: number) => index % 2 === 0

  const getGameStatus = () => {
    if (gameOver) {
      return { text: "Game Over", className: "status-game-over" }
    }
    if (inCheck) {
      return { text: `${currentTurn === 'w' ? 'White' : 'Black'} in Check!`, className: "status-check" }
    }
    return { text: `${currentTurn === 'w' ? 'White' : 'Black'} to move`, className: "status-normal" }
  }

  const status = getGameStatus()

  return (
    <div className="commentary-section">
      <div className="commentary-header">
        <h3 className="commentary-title">Game Analysis</h3>
        <div className={`game-status ${status.className}`}>
          {status.text}
        </div>
      </div>

      <div className="move-history">
        <div className="moves-header">
          <span>Move History</span>
          <span className="move-count">{moveHistory.length} moves</span>
        </div>
        
        <div className="moves-list">
          {moveHistory.length === 0 ? (
            <div className="no-moves">
              <p>Game hasn't started yet</p>
              <p className="move-hint">Make your first move!</p>
            </div>
          ) : (
            <div className="moves-grid">
              {moveHistory.map((move, index) => (
                <div key={index} className="move-entry">
                  {isWhiteMove(index) && (
                    <span className="move-number">{formatMoveNumber(index)}.</span>
                  )}
                  <span className={`move-notation ${isWhiteMove(index) ? 'white-move' : 'black-move'}`}>
                    {move}
                  </span>
                </div>
              ))}
            </div>
          )}
          <div ref={movesEndRef} />
        </div>
      </div>

      <div className="analysis-section">
        <div className="analysis-header">
          <span>Quick Analysis</span>
        </div>
        <div className="analysis-content">
          {moveHistory.length === 0 ? (
            <p className="analysis-text">Start playing to see analysis</p>
          ) : (
            <div className="analysis-stats">
              <div className="stat-item">
                <span className="stat-label">Total Moves</span>
                <span className="stat-value">{moveHistory.length}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Current Turn</span>
                <span className="stat-value">{currentTurn === 'w' ? 'White' : 'Black'}</span>
              </div>
              {inCheck && (
                <div className="stat-item check-warning">
                  <span className="stat-label">Status</span>
                  <span className="stat-value">Check!</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Commentary
