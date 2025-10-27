import { useState } from 'react'
import './pgn-modal.css'

type PgnImportProps = {
  isOpen: boolean
  onClose: () => void
  onImport: (pgn: string) => void
}

function PgnImport({ isOpen, onClose, onImport }: PgnImportProps) {
  const [activeTab, setActiveTab] = useState<'file' | 'text'>('text')
  const [pgnText, setPgnText] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const content = event.target?.result as string
      setPgnText(content)
      setActiveTab('text')
    }
    reader.onerror = () => {
      setError('Failed to read file')
    }
    reader.readAsText(file)
  }

  const handleImport = () => {
    if (!pgnText.trim()) {
      setError('Please enter or upload a PGN')
      return
    }

    try {
      // Basic PGN validation
      if (!pgnText.includes('[') && !pgnText.match(/\d+\./)) {
        setError('Invalid PGN format')
        return
      }

      onImport(pgnText)
      setPgnText('')
      setError(null)
      onClose()
    } catch (err) {
      setError('Failed to import PGN')
    }
  }

  const handleClose = () => {
    setPgnText('')
    setError(null)
    onClose()
  }

  return (
    <div className="pgn-modal-backdrop" onClick={handleClose}>
      <div className="pgn-modal" onClick={(e) => e.stopPropagation()}>
        <header className="pgn-modal-header">
          <h3>Import PGN</h3>
          <button className="pgn-modal-close" onClick={handleClose} aria-label="Close">
            ✕
          </button>
        </header>

        <div className="pgn-import-tabs">
          <button
            className={`pgn-import-tab ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => setActiveTab('text')}
          >
            📝 Paste PGN
          </button>
          <button
            className={`pgn-import-tab ${activeTab === 'file' ? 'active' : ''}`}
            onClick={() => setActiveTab('file')}
          >
            📁 Upload File
          </button>
        </div>

        <div className="pgn-modal-body">
          {activeTab === 'text' ? (
            <textarea
              className="pgn-textarea"
              value={pgnText}
              onChange={(e) => {
                setPgnText(e.target.value)
                setError(null)
              }}
              placeholder="Paste your PGN here..."
              rows={15}
            />
          ) : (
            <div className="pgn-file-upload">
              <label htmlFor="pgn-file-input" className="pgn-file-upload-label">
                <div className="pgn-file-upload-icon">📁</div>
                <p className="pgn-file-upload-text">Click to upload PGN file</p>
                <p className="pgn-file-upload-hint">or drag and drop</p>
              </label>
              <input
                id="pgn-file-input"
                type="file"
                accept=".pgn,.txt"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              {pgnText && (
                <p className="pgn-file-uploaded">✓ File loaded. Switch to "Paste PGN" tab to view.</p>
              )}
            </div>
          )}

          {error && <p className="pgn-error">{error}</p>}
        </div>

        <footer className="pgn-modal-footer">
          <button className="btn-ghost" onClick={handleClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleImport}>
            Import
          </button>
        </footer>
      </div>
    </div>
  )
}

export default PgnImport

