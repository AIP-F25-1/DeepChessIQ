# PGN Format Integration

## Overview
The chess engine works with PGN (Portable Game Notation) format for human-readable game notation, while internally using FEN for position evaluation.

---

## What Changed?

### Before (FEN only):
```
Input:  FEN → Simple Engine
Output: Move object
```

### After (PGN with conversion):
```
Input:  PGN → Convert to FEN → Simple Engine
Output: Move → Display as PGN (e.g., "e5", "Nf3", "O-O")
```

---

## PGN vs UCI vs FEN

| Format | Purpose | Example |
|--------|---------|---------|
| **PGN** | Human-readable game notation | `1. e4 e5 2. Nf3 Nc6 3. Bb5` |
| **FEN** | Board position snapshot | `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1` |
| **UCI** | Engine move format | `e7e5`, `g1f3`, `e1g1` |

---

## Code Changes

### File: `chessiq-ui/src/hooks/useChessGame.ts`

#### Change 1: INPUT - Generate PGN before sending to Stockfish (Lines 85-91)

```typescript
// INPUT: Convert game state to PGN, then PGN to FEN for Stockfish
const currentPgn = engineRef.current.pgn()
const currentFen = engineRef.current.fen()

console.log('📥 INPUT to Stockfish:')
console.log('  PGN:', currentPgn || '(starting position)')
console.log('  FEN (converted):', currentFen)
```

**What this does:**
- Extracts current game in PGN format (e.g., `"1. e4 e5 2. Nf3"`)
- Also extracts FEN (required by Stockfish)
- Logs both formats to console

#### Change 2: OUTPUT - Convert UCI to PGN notation (Lines 97-107)

```typescript
// OUTPUT: Convert UCI move to PGN notation
const uciMove = `${move.from}${move.to}${move.promotion || ''}`

// Apply move temporarily to get PGN notation
const tempChess = new Chess(engineRef.current.fen())
const moveObj = tempChess.move({ from: move.from, to: move.to, promotion: 'q' })
const pgnMove = moveObj ? moveObj.san : uciMove

console.log('📤 OUTPUT from Stockfish:')
console.log('  UCI move:', uciMove)
console.log('  PGN notation:', pgnMove)
```

**What this does:**
- Receives UCI move from Stockfish (e.g., `"e7e5"`)
- Creates temporary chess position
- Applies the move to get SAN (Standard Algebraic Notation) = PGN format
- Logs both UCI and PGN formats

#### Change 3: Export PGN in game state (Line 153)

```typescript
return {
  fen,
  pgn: engineRef.current.pgn(), // Add PGN export
  pieces,
  // ... rest of state
}
```

**What this does:**
- Makes PGN available to all components using `useChessGame()`
- Can access via `game.pgn`

---

## Example Console Output

When you play the game, you'll see in browser console:

```
📥 INPUT to Stockfish:
  PGN: 1. e4
  FEN (converted): rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1

📤 OUTPUT from Stockfish:
  UCI move: e7e5
  PGN notation: e5

📥 INPUT to Stockfish:
  PGN: 1. e4 e5 2. Nf3
  FEN (converted): rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2

📤 OUTPUT from Stockfish:
  UCI move: b8c6
  PGN notation: Nc6
```

---

## PGN Format Examples

### Simple Pawn Moves
```
PGN: e4
UCI: e2e4
```

### Piece Moves
```
PGN: Nf3   (Knight to f3)
UCI: g1f3

PGN: Bb5   (Bishop to b5)
UCI: f1b5
```

### Captures
```
PGN: exd5  (pawn on e-file captures on d5)
UCI: e4d5

PGN: Nxe5  (Knight captures on e5)
UCI: f3e5
```

### Castling
```
PGN: O-O    (kingside castling)
UCI: e1g1

PGN: O-O-O  (queenside castling)
UCI: e1c1
```

### Check/Checkmate
```
PGN: Qh5+   (Queen to h5, check)
UCI: d1h5

PGN: Qf7#   (Queen to f7, checkmate)
UCI: d1f7
```

### Pawn Promotion
```
PGN: e8=Q   (pawn promotes to queen)
UCI: e7e8q

PGN: a1=N   (pawn promotes to knight)
UCI: a2a1n
```

---

## How to Use PGN in Your Components

```typescript
// In any component
import { useChessGame } from '../hooks/useChessGame'

function MyComponent() {
  const game = useChessGame()
  
  // Access PGN
  console.log('Current game PGN:', game.pgn)
  
  // Display PGN
  return (
    <div>
      <h3>Game Notation (PGN)</h3>
      <pre>{game.pgn || 'Game not started'}</pre>
    </div>
  )
}
```

---

## Full Game PGN Example

```
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 
7. Bb3 d6 8. c3 O-O 9. h3 Na5 10. Bc2 c5 11. d4 Qc7
```

---

## Technical Notes

### Why The Engine Uses FEN Internally

The simple chess engine **uses FEN** for position evaluation because:
1. FEN is faster to parse (single string)
2. FEN contains complete position info (not just moves)
3. Enables position-based evaluation

Our code:
- ✅ **Generates PGN** for human readability
- ✅ **Converts to FEN** for engine evaluation
- ✅ **Displays moves in PGN** notation

### Conversion Flow

```
User's Perspective (PGN):
  "1. e4 e5 2. Nf3"
          ↓
Internal (FEN for Engine):
  "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
          ↓
Engine calculates best move:
  from: "b8", to: "c6"
          ↓
Displayed as PGN:
  "Nc6"
```

---

## Files Modified

| File | Lines | What Changed |
|------|-------|--------------|
| `useChessGame.ts` | 99-149 | Added PGN logging in engine move calculation |
| `useChessGame.ts` | 189 | Added PGN to return object |

---

## Testing

1. Start your app: `npm run dev`
2. Open browser console (F12)
3. Make a move
4. Look for logs:
   ```
   📥 INPUT to Engine:
     PGN: ...
     FEN: ...
   
   📤 OUTPUT from Engine:
     UCI move: ...
     PGN notation: ...
   ```

---

## Benefits

✅ **Human-readable** - PGN is standard chess notation  
✅ **Lightweight** - Uses built-in simple engine (no external dependencies)  
✅ **Transparent** - Console logs show both formats  
✅ **Exportable** - Can save games in PGN format  
✅ **Standard** - PGN is universal chess notation  

---

## Next Steps (Optional Enhancements)

1. **Display PGN in UI** - Show move list in PGN notation
2. **Import PGN** - Load games from PGN strings
3. **Export PGN** - Download games as .pgn files
4. **Move navigation** - Click PGN moves to jump to positions

Would you like me to implement any of these features?

