import './commentary.css'
import { useEffect, useRef, useState } from 'react'
import { commentaryApi } from '../../services/commentary'

type CommentaryProps = {
  moveHistory: string[]
  currentTurn: 'w' | 'b'
  inCheck: boolean
  gameOver: boolean
  fen: string
}

function Commentary({ moveHistory, currentTurn, inCheck, gameOver, fen }: CommentaryProps) {
  const movesContainerRef = useRef<HTMLDivElement>(null)
  const movesEndRef = useRef<HTMLDivElement>(null)
  const commentaryAbortRef = useRef<AbortController | null>(null)
  const [commentary, setCommentary] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  useEffect(() => {
    if (moveHistory.length === 0) {
      commentaryAbortRef.current?.abort()
      commentaryAbortRef.current = null
      setCommentary(null)
      setError(null)
      setIsLoading(false)
      return
    }

    const latestMove = moveHistory[moveHistory.length - 1]
    const controller = new AbortController()

    // Abort any in-flight request before starting a new one
    commentaryAbortRef.current?.abort()
    commentaryAbortRef.current = controller

    const fetchCommentary = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await commentaryApi.getMoveCommentary(
          {
            fen: fen || null,
            move: latestMove,
          },
          controller.signal,
        )

        const text =
          typeof response.commentary === 'string' && response.commentary.trim().length > 0
            ? response.commentary.trim()
            : typeof response.summary === 'string' && response.summary.trim().length > 0
            ? response.summary.trim()
            : null

        if (text) {
          setCommentary(text)
        } else {
          setCommentary('Commentary is not available for this move yet.')
        }
      } catch (err: any) {
        if (err?.name === 'AbortError') {
          return
        }
        console.error('[Commentary] Failed to fetch commentary:', err)
        setError('Unable to fetch commentary right now.')
        setCommentary(null)
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    fetchCommentary()

    return () => {
      controller.abort()
    }
  }, [moveHistory, fen])

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
          ) : isLoading ? (
            <p className="commentary-text commentary-loading">Fetching commentary...</p>
          ) : error ? (
            <p className="commentary-text commentary-error">{error}</p>
          ) : commentary ? (
            <p className="commentary-text">{commentary}</p>
          ) : (
            <p className="commentary-text commentary-empty">Commentary is not available for this move yet.</p>
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
