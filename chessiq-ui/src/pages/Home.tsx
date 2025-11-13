import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import Navbar from '../components/navbar/Navbar'
import ChessBoard from '../components/chessboard/ChessBoard'
import Commentary from '../components/commentary/Commentary'
import PgnExport from '../components/game/PgnExport'
import PgnImport from '../components/game/PgnImport'
import { useChessGame } from '../hooks/useChessGame'
import { gamesApi } from '../services/api'
import './home.css'

function HomePage() {
  const { user } = useAuth()
  const game = useChessGame()
  const { moveHistory, turn, inCheck, gameOver, pgn, loadPgn, gameStartAt, lastMoveAt, fen } = game
  const [showExportModal, setShowExportModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [gameSaved, setGameSaved] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  // Auto-save game when it's over
  useEffect(() => {
    const saveGame = async () => {
      // Only save if game is over, user is logged in, game hasn't been saved yet, and there are moves
      if (!gameOver || !user || gameSaved || moveHistory.length === 0) {
        return
      }

      try {
        // Determine result based on game state
        // This is a simplified version - you might want to enhance this logic
        const result = turn === 'w' ? 'loss' : 'win' // If it's white's turn and game is over, white lost
        
        // Calculate duration in seconds
        const durationSeconds = lastMoveAt && gameStartAt 
          ? Math.floor((lastMoveAt - gameStartAt) / 1000) 
          : 0

        // Estimate rating change (simplified - in reality this would be calculated based on game outcome)
        const ratingChange = result === 'win' ? 12 : result === 'loss' ? -8 : 0

        const response = await gamesApi.save({
          result: result as 'win' | 'loss' | 'draw',
          userColor: 'w', // Player always plays white (bot is black)
          totalMoves: moveHistory.length,
          timeControl: '10+0',
          ratingChange,
          durationSeconds,
          pgn,
        })

        setGameSaved(true)
        setSaveMessage(`Game saved! New rating: ${response.newRating}`)
        
        // Hide message after 5 seconds
        setTimeout(() => setSaveMessage(null), 5000)
      } catch (error) {
        console.error('Failed to save game:', error)
        setSaveMessage('Failed to save game')
        setTimeout(() => setSaveMessage(null), 5000)
      }
    }

    saveGame()
  }, [gameOver, user, gameSaved, moveHistory.length, pgn, turn, lastMoveAt, gameStartAt])

  const handleExportPgn = () => {
    setShowExportModal(true)
  }

  const handleImportPgn = (pgnText: string) => {
    const success = loadPgn(pgnText)
    if (success) {
      console.log('PGN imported successfully')
      setGameSaved(false) // Reset saved flag when importing a new game
    } else {
      console.error('Failed to import PGN')
    }
  }

  return (
    <div className="home">
      <Navbar />
      {saveMessage && (
        <div className="save-message">
          {saveMessage}
        </div>
      )}
      <main className="home-main">
        <div className="home-game-layout">
          <section className="home-board">
            <ChessBoard
              pieces={game.pieces}
              selected={game.selected as any}
              setSelected={game.setSelected as any}
              legalMovesFrom={game.legalMovesFrom as any}
              tryMove={game.tryMove as any}
              turn={game.turn as any}
              lastMove={game.lastMove as any}
              gameStartAt={game.gameStartAt}
              lastMoveAt={game.lastMoveAt}
              eliminatedPieces={game.eliminatedPieces as any}
              engineSide={game.engineSide as any}
              isEngineThinking={game.isEngineThinking}
              onImportPgn={() => setShowImportModal(true)}
              onExportPgn={handleExportPgn}
              canExport={moveHistory.length > 0}
            />
          </section>
          
          <aside className="home-right-sidebar">
            <Commentary 
              moveHistory={moveHistory}
              currentTurn={turn}
              inCheck={inCheck}
              gameOver={gameOver}
              fen={fen}
            />
          </aside>
        </div>
      </main>

      <PgnExport
        pgn={pgn}
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
      />
      <PgnImport
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImportPgn}
      />
    </div>
  )
}

export default HomePage


