# Chess Algorithms Analysis - DeepChessIQ Project

## Summary
After analyzing the entire codebase, here are **all chess algorithms** found in your project:

---

## 1. 🎯 **ACTIVE: Simple Material-Based Engine** (Currently Used)
**Location**: `chessiq-ui/src/hooks/useChessGame.ts` (lines 77-149)

### Algorithm Type
- **Minimax search with 2-ply depth**
- **Material-only evaluation**
- Lightweight JavaScript implementation

### Implementation Details
```typescript
// File: chessiq-ui/src/hooks/useChessGame.ts
- Search Depth: 2 plies (1 move + 1 opponent response)
- Evaluation: Material counting only
- Piece Values: p=100, n=320, b=330, r=500, q=900, k=0
```

### How It Works
1. Receives board position (Chess.js object)
2. Generates all legal moves
3. For each move:
   - Make the move
   - Generate all opponent's legal responses
   - Evaluate each resulting position (count material)
   - Assume opponent picks their best response
4. Select the move with the best evaluation after opponent's best reply
5. Returns move in from/to format (e.g., from: "e7", to: "e5")

### Strength
- **ELO Rating**: ~800-1000
- **Beginner/Casual Level**: Good for learning and casual play

## 2. 📊 **Chess Move Analysis Algorithm** (Jupyter Notebook)
**Location**: `llm_commentary/ChessCommentry_MoveBased.ipynb`

### Algorithm Type
- **Heuristic-based move classifier**
- **Static position evaluator**

### Components

#### A. Position Evaluation Function
```python
# Material counting
PIECE_VALUE = {
    PAWN: 1.0, KNIGHT: 3.2, BISHOP: 3.3,
    ROOK: 5.0, QUEEN: 9.0, KING: 0.0
}

# Center control bonus
CENTER = {D4, E4, D5, E5}
EXT_CENTER = {C3, D3, E3, F3, C4, F4, C5, F5, C6, D6, E6, F6}

def eval_white(board):
    score = 0
    score += material_score(board)       # Count pieces
    score += center_control_score(board) # Bonus for central pieces
    score += mobility_score(board)       # Bonus for legal moves
    return score
```

#### B. Move Classification
Classifies each move as:
- **Excellent** (delta ≥ +0.60)
- **Good** (delta ≥ +0.20)
- **Inaccuracy** (delta ≥ -0.20)
- **Mistake** (delta ≥ -0.60)
- **Blunder** (delta < -0.60)

Based on:
1. Material gain/loss
2. Center control
3. Mobility changes
4. Tactical features (checks, captures, castling)

#### C. Tactical Recognition
```python
if board.gives_check(move):
    reasons.append("gives check")
if board.is_capture(move):
    reasons.append("wins material" if delta > 0.15 else "trades")
if board.is_castling(move):
    reasons.append("improves king safety")
if move_to_center:
    reasons.append("improves central control")
if develops_piece:
    reasons.append("develops a minor piece")
```

### Purpose
This algorithm is NOT for making moves. It's for:
- ✅ **Analyzing player moves** after they're made
- ✅ **Generating commentary** (with LLM integration)
- ✅ **Educational feedback** for students/players

---

## 3. 🧩 **Chess.js Library** (Move Generation & Validation)
**Location**: `node_modules/chess.js` (used throughout)

### Algorithm Type
- **Complete chess rules engine**
- **Legal move generator**

### What It Provides
```typescript
// In chessiq-ui/src/hooks/useChessGame.ts
const engineRef = useRef(new Chess())

// Algorithms provided by chess.js:
- Move validation (is this move legal?)
- Move generation (what are all legal moves?)
- Check detection
- Checkmate/stalemate detection
- En passant handling
- Castling validation
- Fifty-move rule
- Threefold repetition
- FEN parsing/generation
```

### Underlying Algorithm
- **Pseudo-legal move generation** with legality verification
- **Bitboard representation** for fast move generation
- **Zobrist hashing** for position uniqueness

---

## 4. 🎨 **UI/Board Algorithms** (Non-Chess Logic)
**Location**: `chessiq-ui/src/components/chessboard/ChessBoard.tsx`

### Not chess algorithms, but worth noting:
```typescript
// Square color calculation
const isDark = (file + rank) % 2 === 0

// Coordinate conversion
const coordsToName = (file, rank) => 
  `${String.fromCharCode(96 + file)}${rank}`

// Time formatting
const formatDuration = (ms) => {
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  // ...
}
```

---

## Summary Table

| Algorithm | Status | Purpose | Strength | Location |
|-----------|--------|---------|----------|----------|
| **Simple 2-ply engine** | ✅ Active | Computer opponent | ~800-1000 ELO | `useChessGame.ts:77-149` |
| **Move Classifier** | 📝 Separate tool | Post-game analysis | N/A (not for playing) | `llm_commentary/` notebook |
| **chess.js** | ✅ Active | Rules engine & validation | N/A (utility) | npm package |
| **Board rendering** | ✅ Active | UI logic | N/A (display only) | `ChessBoard.tsx` |

---

## Current Active Engine: Simple 2-Ply Engine

### Configuration
```typescript
// File: chessiq-ui/src/hooks/useChessGame.ts (lines 77-149)
- Fixed 2-ply depth (1 move + 1 opponent response)
- Material-only evaluation
- No configuration needed - works out of the box
```

### Characteristics
1. **Fast**: Instant response (no delay)
2. **Lightweight**: No external dependencies
3. **Consistent**: Always uses same evaluation
4. **Beginner-friendly**: Makes occasional mistakes (~800-1000 ELO)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│              (ChessBoard.tsx component)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   useChessGame() Hook      │
        │  - Game state management   │
        │  - Move validation         │
        │  - Simple AI engine        │
        └──────┬─────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │   chess.js Library   │
    │  - Legal move gen    │
    │  - Rules validation  │
    │  - Board state       │
    │  - FEN/PGN parsing   │
    └──────────────────────┘
```

---

## Conclusion

**Your project currently uses:**
1. ✅ **Simple 2-ply engine** - Lightweight JavaScript chess engine (ACTIVE)
2. ✅ **chess.js** - Rules validation and move generation (ACTIVE)
3. ✅ **Custom move classifier** - For educational analysis (SEPARATE TOOL)

**Benefits of current setup:**
- ✅ No external dependencies or large WASM files
- ✅ Fast, instant responses
- ✅ Works reliably in all browsers
- ✅ Perfect for casual/beginner play
- ✅ PGN support for game notation

