import './chessboard.css'
import { useEffect, useState } from 'react'
import { useChessGame } from '../hooks/useChessGame'
import EliminatedPieces from './EliminatedPieces'

type Square = {
  file: number
  rank: number
  isDark: boolean
}

function buildBoard(): Square[] {
  const squares: Square[] = []
  for (let rank = 8; rank >= 1; rank -= 1) {
    for (let file = 1; file <= 8; file += 1) {
      const isDark = (file + rank) % 2 === 0
      squares.push({ file, rank, isDark })
    }
  }
  return squares
}

function ChessBoard() {
  const squares = buildBoard()
  const { pieces, selected, setSelected, legalMovesFrom, tryMove, turn, lastMove, gameStartAt, lastMoveAt, eliminatedPieces } = useChessGame()
  const [nowTs, setNowTs] = useState<number>(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNowTs(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const formatDuration = (ms: number) => {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000))
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60
    if (hours > 0) return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    return `${minutes}:${String(seconds).padStart(2, '0')}`
  }

  const coordsToName = (file: number, rank: number) => `${String.fromCharCode(96 + file)}${rank}` as const

  const handleSquareClick = (file: number, rank: number) => {
    const name = coordsToName(file, rank) as any
    if (selected) {
      if (selected === name) {
        setSelected(null)
        return
      }
      const legalTargets = legalMovesFrom(selected)
      if (legalTargets.includes(name)) {
        tryMove(selected as any, name as any)
        return
      }
      // if clicked friendly piece, switch selection
      const targetPiece = pieces.find((p) => p.square === name)
      const selectedPiece = pieces.find((p) => p.square === selected)
      if (targetPiece && selectedPiece && targetPiece.color === selectedPiece.color) {
        setSelected(name)
      } else {
        setSelected(null)
      }
    } else {
      // select only if it's the side to move
      const piece = pieces.find((p) => p.square === name)
      if (piece && ((turn === 'w' && piece.color === 'w') || (turn === 'b' && piece.color === 'b'))) {
        setSelected(name)
      }
    }
  }

  const renderPiece = (squareName: string) => {
    const piece = pieces.find((p) => p.square === (squareName as any))
    if (!piece) return null
    const key = `${piece.square}-${piece.type}-${piece.color}`
    const code = `${piece.color === 'w' ? 'w' : 'b'}${piece.type.toUpperCase()}`
    const src = `https://lichess1.org/assets/piece/cburnett/${code}.svg`
    return <img key={key} className="piece-img" src={src} alt={code} draggable={false} />
  }

  return (
    <div className="chessboard-wrapper">
      <div className="left-sidebar">
        <div className="timers-bar" aria-label="Game timers">
          <div className="timer-card">
            <span className="timer-label">Total</span>
            <span className="timer-value">{formatDuration(nowTs - gameStartAt)}</span>
          </div>
          <div className="timer-card">
            <span className="timer-label">Since last move</span>
            <span className="timer-value">{formatDuration(lastMoveAt ? nowTs - lastMoveAt : nowTs - gameStartAt)}</span>
          </div>
        </div>
        <div className="eliminated-pieces-section">
          <EliminatedPieces 
            pieces={eliminatedPieces}
            playerColor="w"
            playerName="White Player"
          />
          <EliminatedPieces 
            pieces={eliminatedPieces}
            playerColor="b"
            playerName="Black Player"
          />
        </div>
      </div>
      <div className="board-stack">
        <div className="chessboard-grid" role="grid" aria-label="Chessboard">
        {squares.map((sq) => {
          const name = coordsToName(sq.file, sq.rank)
          const isSelected = selected === (name as any)
          const isLastMove = lastMove ? lastMove.from === (name as any) || lastMove.to === (name as any) : false
          const isTarget = selected ? legalMovesFrom(selected).includes(name as any) : false
          return (
            <button
              type="button"
              key={`${sq.file}-${sq.rank}`}
              className={`square ${sq.isDark ? 'dark' : 'light'} ${isSelected ? 'selected' : ''} ${isTarget ? 'target' : ''} ${isLastMove ? 'last-move' : ''}`}
              aria-label={`Square ${name}`}
              onClick={() => handleSquareClick(sq.file, sq.rank)}
            >
              {renderPiece(name)}
              <span className="coord">
                {sq.file === 1 ? sq.rank : ''}
                {sq.rank === 1 ? String.fromCharCode(96 + sq.file) : ''}
              </span>
            </button>
          )
        })}
        </div>
        <div className="board-axes">
          <div className="files">
            {['a','b','c','d','e','f','g','h'].map((f) => (
              <span key={f}>{f}</span>
            ))}
          </div>
          <div className="ranks">
            {[8,7,6,5,4,3,2,1].map((r) => (
              <span key={r}>{r}</span>
            ))}
          </div>
        </div>
      </div>
      <div className="right-spacer" aria-hidden="true" />
    </div>
  )
}

export default ChessBoard


