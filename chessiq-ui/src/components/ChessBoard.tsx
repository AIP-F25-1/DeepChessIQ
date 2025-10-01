import './chessboard.css'

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
  return (
    <div className="chessboard-wrapper">
      <div className="chessboard-grid" role="grid" aria-label="Chessboard">
        {squares.map((sq) => (
          <div
            key={`${sq.file}-${sq.rank}`}
            className={`square ${sq.isDark ? 'dark' : 'light'}`}
            role="gridcell"
            aria-label={`Square ${String.fromCharCode(96 + sq.file)}${sq.rank}`}
          />
        ))}
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
  )
}

export default ChessBoard


