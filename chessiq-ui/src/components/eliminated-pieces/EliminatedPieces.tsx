import './eliminated-pieces.css'
import { type EliminatedPiece } from '../../hooks/useChessGame'

type EliminatedPiecesProps = {
  pieces: EliminatedPiece[]
  playerColor: 'w' | 'b'
  playerName: string
}

function EliminatedPieces({ pieces, playerColor, playerName }: EliminatedPiecesProps) {
  // Filter pieces that were eliminated from this player (captured by the opponent)
  const capturedPieces = pieces.filter(piece => piece.color === playerColor)
  
  // Group pieces by type for better display
  const groupedPieces = capturedPieces.reduce((acc, piece) => {
    if (!acc[piece.type]) {
      acc[piece.type] = []
    }
    acc[piece.type].push(piece)
    return acc
  }, {} as Record<string, EliminatedPiece[]>)

  // Calculate material advantage
  const pieceValues: Record<string, number> = {
    'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0
  }
  
  const materialValue = capturedPieces.reduce((sum, piece) => sum + pieceValues[piece.type], 0)

  const renderPiece = (piece: EliminatedPiece, index: number) => {
    const code = `${piece.color === 'w' ? 'w' : 'b'}${piece.type.toUpperCase()}`
    const src = `https://lichess1.org/assets/piece/cburnett/${code}.svg`
    return (
      <img 
        key={`${piece.type}-${piece.color}-${index}`}
        className="eliminated-piece-img" 
        src={src} 
        alt={`${piece.color} ${piece.type}`} 
        draggable={false} 
      />
    )
  }

  return (
    <div className="eliminated-pieces-card">
      <div className="eliminated-pieces-header">
        <h3 className="player-name">{playerName}</h3>
        {materialValue > 0 && (
          <span className="material-advantage">+{materialValue}</span>
        )}
      </div>
      <div className="eliminated-pieces-grid">
        {capturedPieces.length === 0 ? (
          <p className="no-captures">No captures yet</p>
        ) : (
          // Order pieces by value (highest first)
          Object.entries(groupedPieces)
            .sort(([a], [b]) => pieceValues[b] - pieceValues[a])
            .map(([type, pieces]) => (
              <div key={type} className="piece-group">
                {pieces.map((piece, index) => renderPiece(piece, index))}
              </div>
            ))
        )}
      </div>
    </div>
  )
}

export default EliminatedPieces
