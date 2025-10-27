import { useState } from 'react'
import Navbar from '../components/navbar/Navbar'
import ChessBoard from '../components/chessboard/ChessBoard'
import Commentary from '../components/commentary/Commentary'
import PgnExport from '../components/game/PgnExport'
import PgnImport from '../components/game/PgnImport'
import { useChessGame } from '../hooks/useChessGame'
import './home.css'

function HomePage() {
  const game = useChessGame()
  const { moveHistory, turn, inCheck, gameOver, pgn, loadPgn } = game
  const [showExportModal, setShowExportModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)

  const handleExportPgn = () => {
    setShowExportModal(true)
  }

  const handleImportPgn = (pgnText: string) => {
    const success = loadPgn(pgnText)
    if (success) {
      console.log('PGN imported successfully')
    } else {
      console.error('Failed to import PGN')
    }
  }

  return (
    <div className="home">
      <Navbar />
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


