import './commentary.css'
import { useEffect, useRef } from 'react'

type CommentaryProps = {
  moveHistory: string[]
  currentTurn: 'w' | 'b'
  inCheck: boolean
  gameOver: boolean
}

function Commentary({ moveHistory, currentTurn, inCheck, gameOver }: CommentaryProps) {
  const movesContainerRef = useRef<HTMLDivElement>(null)
  const movesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll the moves panel without affecting page scroll
  useEffect(() => {
    const container = movesContainerRef.current
    if (!container) return
    // Keep user position if they scrolled up; only autoscroll when near bottom
    const threshold = 60
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold
    if (isNearBottom) {
      container.scrollTop = container.scrollHeight
    }
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

  const getRandomCommentary = () => {
    const commentaries = [
      "An interesting opening choice by White! Both players are developing their pieces rapidly towards the center. The game is following classical principles with good control of key squares. It will be fascinating to see how the position unfolds as we transition into the middlegame phase.",
      "The position is heating up with tension building in the center. White appears to have a slight initiative with better piece coordination, but Black's solid pawn structure provides a strong defensive foundation. Strategic planning will be crucial for both sides moving forward.",
      "Black's pawn structure looks remarkably solid with no apparent weaknesses. The defensive setup demonstrates good understanding of positional chess principles. White will need to find creative ways to create attacking opportunities or risk a balanced endgame where Black's solid position could prove advantageous.",
      "A tactical opportunity is emerging as the center becomes increasingly dynamic. Both players must be vigilant for tactical shots involving piece exchanges and pawn breaks. The next few moves will be critical in determining the character of the resulting middlegame position.",
      "Material is perfectly equal on the board, but the position clearly favors the side with more active piece placement. Controlling open files and diagonals will be key to gaining a meaningful advantage. Watch how the players maneuver their pieces to dominate critical squares.",
      "This game is remarkably well-balanced with both sides having equal chances for victory. Neither player has committed any significant errors yet, and the position remains rich with possibilities. The outcome will likely be determined by who can execute their plan more precisely in the critical middlegame phase.",
      "The middlegame is rapidly approaching, and strategic planning becomes absolutely crucial at this stage. Players must carefully consider their pawn breaks, piece placement, and king safety. One hasty move could tip the balance decisively in favor of the opponent, so patience and precision are essential.",
      "Excellent development by both players! The fight for central control is intense with neither side willing to concede the initiative. The position demonstrates textbook opening principles being applied effectively. We can expect a sharp and exciting game as both sides have built solid foundations for their attacking ambitions.",
      "The pawn structure will play a decisive role in the approaching endgame. Weak pawns could become targets, while strong pawn chains provide safety and structure. Both players should be thinking several moves ahead, considering how the current pawn configuration might influence the game's final outcome.",
      "A classical approach to the opening, demonstrating time-tested principles of chess strategy. This solid and reliable method has been employed by grandmasters for decades. The resulting position offers a balanced game with opportunities for both tactical shots and strategic maneuvering as play continues to develop.",
    ]
    return commentaries[moveHistory.length % commentaries.length]
  }

  return (
    <div className="commentary-section">
      <div className="commentary-header">
        <h3 className="commentary-title">Game Analysis</h3>
        <div className={`game-status ${status.className}`}>
          {status.text}
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

      <div className="commentary-box">
        <div className="commentary-box-header">
          <span>💬 Commentary</span>
        </div>
        <div className="commentary-box-content">
          {moveHistory.length === 0 ? (
            <p className="commentary-text">Game commentary will appear here as you play...</p>
          ) : (
            <p className="commentary-text">{getRandomCommentary()}</p>
          )}
        </div>
      </div>

      <div className="move-history">
        <div className="moves-header">
          <span>Move History</span>
          <span className="move-count">{moveHistory.length} moves</span>
        </div>
        
        <div className="moves-list" ref={movesContainerRef}>
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
    </div>
  )
}

export default Commentary
