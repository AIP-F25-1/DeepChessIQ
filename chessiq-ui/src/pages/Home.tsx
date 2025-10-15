import Navbar from '../components/navbar/Navbar'
import ChessBoard from '../components/chessboard/ChessBoard'
import Commentary from '../components/commentary/Commentary'
import { useChessGame } from '../hooks/useChessGame'
import './home.css'

function HomePage() {
  const game = useChessGame()
  const { moveHistory, turn, inCheck, gameOver } = game

  return (
    <div className="home">
      <Navbar />
      <main className="home-main">
        <div className="home-game-layout">
          <section className="home-board">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
              {/* <span style={{ fontSize: '0.9rem', color: '#9aa1b5' }}>Opponent: Computer (plays Black)</span> */}
            </div>
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
    </div>
  )
}

export default HomePage


