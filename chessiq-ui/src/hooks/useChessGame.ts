import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
  const [engineSide, setEngineSide] = useState<Color | null>('b')
  const [isEngineThinking, setIsEngineThinking] = useState<boolean>(false)
  const ENGINE_URL = (import.meta as any).env?.VITE_ENGINE_URL || '/engine/bestmove'
  const ENGINE_TIMEOUT_MS = Number((import.meta as any).env?.VITE_ENGINE_TIMEOUT_MS || 10000)

  const pieces: BoardPiece[] = useMemo(() => {
    const result: BoardPiece[] = []
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

  const tryMove = useCallback(
    (from: SquareName, to: SquareName) => {
      const res = engineRef.current.move({ from, to, promotion: 'q' as const })
      if (res) {
        if (res.captured) {
          setEliminatedPieces((prev) => [
            ...prev,
            {
              type: res.captured as 'p' | 'n' | 'b' | 'r' | 'q' | 'k',
              color: res.color === 'w' ? 'b' : 'w',
            },
          ])
        }

        setMoveHistory((prev) => [...prev, res.san])
        setFen(engineRef.current.fen())
        setLastMove({ from: res.from as SquareName, to: res.to as SquareName })
        setSelected(null)
        setLastMoveAt(Date.now())
        return true
      }
      return false
    },
    [],
  )

  // Hosted engine with local fallback
  const getEngineMove = useCallback(async (): Promise<{ from: SquareName; to: SquareName } | null> => {
    const fenNow = engineRef.current.fen()
    // Try remote engine first
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), ENGINE_TIMEOUT_MS)
      const payload = { fen: fenNow }
      const resp = await fetch(ENGINE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      if (resp.ok) {
        const data: any = await resp.json()
        const uci: string | undefined = data?.uci || data?.bestmove || data?.move
        if (uci && typeof uci === 'string' && uci.length >= 4) {
          const from = uci.slice(0, 2) as SquareName
          const to = uci.slice(2, 4) as SquareName
          return { from, to }
        }
      }
    } catch (e) {
      console.warn('[ENGINE] Remote call failed, falling back to local engine', e)
      // ignore and fallback
    }

    // Fallback simple depth-2 engine
    const pieceValues: Record<string, number> = { p: 100, n: 320, b: 330, r: 500, q: 900, k: 0 }
    const evaluate = (ch: Chess) => {
      const board = ch.board()
      let score = 0
      for (const rank of board) {
        for (const sq of rank) {
          if (!sq) continue
          const val = pieceValues[sq.type]
          score += sq.color === 'w' ? val : -val
        }
      }
      return score
    }
    const sideToMove = engineRef.current.turn() as Color
    const root = new Chess(engineRef.current.fen())
    const moves = root.moves({ verbose: true }) as Move[]
    if (!moves.length) return null
    let bestScore = sideToMove === 'w' ? -Infinity : Infinity
    let best: Move | null = null
    for (const mv of moves) {
      const ch1 = new Chess(root.fen())
      ch1.move({ from: mv.from as SquareName, to: mv.to as SquareName, promotion: 'q' })
      const replies = ch1.moves({ verbose: true }) as Move[]
      let replyScore: number
      if (replies.length === 0) {
        replyScore = evaluate(ch1)
      } else {
        let oppBest = sideToMove === 'w' ? Infinity : -Infinity
        for (const rep of replies) {
          const ch2 = new Chess(ch1.fen())
          ch2.move({ from: rep.from as SquareName, to: rep.to as SquareName, promotion: 'q' })
          const sc = evaluate(ch2)
          if (sideToMove === 'w') {
            if (sc < oppBest) oppBest = sc
          } else {
            if (sc > oppBest) oppBest = sc
          }
        }
        replyScore = oppBest
      }
      if (sideToMove === 'w') {
        if (replyScore > bestScore) { bestScore = replyScore; best = mv }
      } else {
        if (replyScore < bestScore) { bestScore = replyScore; best = mv }
      }
    }
    const chosen = best || moves[0]
    return { from: chosen.from as SquareName, to: chosen.to as SquareName }
  }, [])

  // Trigger engine move when it's engine's turn (guarded to avoid double-queues)
  const turn: Color = engineRef.current.turn() as Color
  const isGameOver = engineRef.current.isGameOver?.() ?? engineRef.current.isGameOver()
  

  useEffect(() => {
    if (isGameOver) return
    if (!engineSide || turn !== engineSide) return
    if (isEngineThinking) return

    setIsEngineThinking(true)
    
    let cancelled = false
    const executeMove = async () => {
      try {
        const move = await getEngineMove()
        if (!cancelled && move) {
          tryMove(move.from, move.to)
        }
      } catch (error) {
        console.error('[ENGINE] Error during move execution:', error)
      } finally {
        if (!cancelled) {
          setIsEngineThinking(false)
        }
      }
    }

    executeMove()

    return () => {
      cancelled = true
    }
  }, [engineSide, turn, isGameOver])

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
    setIsEngineThinking(false)
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
    engineSide,
    setEngineSide,
    isEngineThinking,
  }
}


