import { useCallback, useMemo, useRef, useState } from 'react'
import { Chess, type Color, type Move, type Square as SquareName } from 'chess.js'

export type BoardPiece = {
  square: SquareName
  type: 'p' | 'n' | 'b' | 'r' | 'q' | 'k'
  color: Color
}

export type EliminatedPiece = {
  type: 'p' | 'n' | 'b' | 'r' | 'q' | 'k'
  color: Color
}

export function useChessGame() {
  const engineRef = useRef(new Chess())
  const [fen, setFen] = useState(engineRef.current.fen())
  const [lastMove, setLastMove] = useState<{ from: SquareName; to: SquareName } | null>(null)
  const [selected, setSelected] = useState<SquareName | null>(null)
  const [gameStartAt, setGameStartAt] = useState<number>(() => Date.now())
  const [lastMoveAt, setLastMoveAt] = useState<number | null>(null)
  const [eliminatedPieces, setEliminatedPieces] = useState<EliminatedPiece[]>([])
  const [moveHistory, setMoveHistory] = useState<string[]>([])

  const pieces: BoardPiece[] = useMemo(() => {
    //const board = engineRef.current.board()
    const result: BoardPiece[] = []
    // chess.js board is 8x8 [rank][file] with a-f names; we'll compute square names
    for (let rank = 8; rank >= 1; rank -= 1) {
      for (let file = 1; file <= 8; file += 1) {
        const squareName = (String.fromCharCode(96 + file) + rank) as SquareName
        const piece = engineRef.current.get(squareName)
        if (piece) {
          result.push({ square: squareName, type: piece.type, color: piece.color })
        }
      }
    }
    return result
  }, [fen])

  const legalMovesFrom = useCallback(
    (from: SquareName): SquareName[] => {
      const moves = engineRef.current.moves({ square: from, verbose: true }) as Move[]
      return moves.map((m) => m.to as SquareName)
    },
    [],
  )

  const tryMove = useCallback((from: SquareName, to: SquareName) => {
    const res = engineRef.current.move({ from, to, promotion: 'q' as const })
    if (res) {
      // Track eliminated piece if there was a capture
      if (res.captured) {
        setEliminatedPieces(prev => [...prev, { 
          type: res.captured as 'p' | 'n' | 'b' | 'r' | 'q' | 'k', 
          color: res.color === 'w' ? 'b' : 'w' // captured piece is opposite color
        }])
      }
      
      // Add move to history
      setMoveHistory(prev => [...prev, res.san])
      
      setFen(engineRef.current.fen())
      setLastMove({ from: res.from as SquareName, to: res.to as SquareName })
      setSelected(null)
      setLastMoveAt(Date.now())
      return true
    }
    return false
  }, [])

  const reset = useCallback(() => {
    engineRef.current = new Chess()
    setFen(engineRef.current.fen())
    setSelected(null)
    setLastMove(null)
    setEliminatedPieces([])
    setMoveHistory([])
    const now = Date.now()
    setGameStartAt(now)
    setLastMoveAt(null)
  }, [])

  return {
    fen,
    pieces,
    selected,
    setSelected,
    legalMovesFrom,
    tryMove,
    reset,
    lastMove,
    gameStartAt,
    lastMoveAt,
    eliminatedPieces,
    moveHistory,
    turn: engineRef.current.turn() as Color,
    inCheck: engineRef.current.inCheck?.() ?? engineRef.current.isCheck?.(),
    gameOver: engineRef.current.isGameOver?.() ?? engineRef.current.isGameOver(),
  }
}


