import Navbar from '../components/Navbar'
import ChessBoard from '../components/ChessBoard'
import './home.css'

function HomePage() {
  return (
    <div className="home">
      <Navbar />
      <main className="home-main">
        <section className="home-board">
          <ChessBoard />
        </section>
      </main>
    </div>
  )
}

export default HomePage


