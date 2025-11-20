import { useState } from 'react'
import './pgn-modal.css'

type PgnExportProps = {
  pgn: string
  isOpen: boolean
  onClose: () => void
}

function PgnExport({ pgn, isOpen, onClose }: PgnExportProps) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pgn)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy PGN:', error)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([pgn], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `chess-game-${Date.now()}.pgn`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="pgn-modal-backdrop" onClick={onClose}>
      <div className="pgn-modal" onClick={(e) => e.stopPropagation()}>
        <header className="pgn-modal-header">
          <h3>Export PGN</h3>
          <button className="pgn-modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>

        <div className="pgn-modal-body">
          <textarea
            className="pgn-textarea"
            value={pgn}
            readOnly
            rows={15}
          />
        </div>

        <footer className="pgn-modal-footer">
          <button className="btn-ghost" onClick={onClose}>
            Close
          </button>
          <button className="btn-primary" onClick={handleCopy}>
            {copied ? '✓ Copied!' : '📋 Copy to Clipboard'}
          </button>
          <button className="btn-primary" onClick={handleDownload}>
            💾 Download .pgn
          </button>
        </footer>
      </div>
    </div>
  )
}

export default PgnExport

