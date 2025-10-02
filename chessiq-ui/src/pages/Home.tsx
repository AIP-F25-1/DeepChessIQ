import Navbar from '../components/navbar/Navbar'
import ChessBoard from '../components/chessboard/ChessBoard'
import Commentary from '../components/commentary/Commentary'
import { useChessGame } from '../hooks/useChessGame'
import './home.css'

function HomePage() {
  const { moveHistory, turn, inCheck, gameOver } = useChessGame()

  return (
    <div className="home">
      <Navbar />
      <main className="home-main">
        <div className="home-game-layout">
          <section className="home-board">
            <ChessBoard />
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


