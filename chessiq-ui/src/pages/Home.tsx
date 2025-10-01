import Navbar from '../components/Navbar'
import ChessBoard from '../components/ChessBoard'
import './home.css'

function HomePage() {
  return (
    <div className="home">
      <Navbar />
      <main className="home-main">
        <section className="home-hero">
          <h1 className="home-title">Welcome to ChessIQ</h1>
          <p className="home-subtitle">Play a quick game or explore the dashboard.</p>
        </section>
        <section className="home-board">
          <ChessBoard />
        </section>
      </main>
    </div>
  )
}

export default HomePage


