# ai/engine/engine_service.py
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import dotenv_values
from stockfish import Stockfish

# Optional: use python-chess for robust FEN validation (works across wrapper versions)
# FEN means Forsyth-Edwards Notation, a standard notation for describing chess positions.
# Chess Board FEN-like Representation Rules:
# ------------------------------------------
# Pieces:
#   - P (Pawn), N (Knight), B (Bishop), R (Rook), Q (Queen), K (King)
#   - Uppercase = White pieces, lowercase = Black pieces
#
# Empty Squares:
#   - Consecutive empty squares are represented by a number
#   - Example: "1" = one empty square, "2" = two empty squares, etc.
#
# Ranks:
#   - Each rank (row) is separated by a forward slash "/"
#
# Board Orientation:
#   - Board is described from White’s perspective
#   - Starts from top-left (a8) to top-right (h8)
#   - Then proceeds rank by rank down to the bottom (a1 → h1)

# If python-chess is not available, we'll fall back to Stockfish's own validation if possible.
try:
    import chess

    HAVE_CHESS = True
except Exception:
    HAVE_CHESS = False

# Configuration and initialization of the Stockfish engine.
# --- config ---
cfg = {**dotenv_values(".env"), **os.environ}
ENGINE_PATH = cfg.get("ENGINE_PATH") or "ai/tools/stockfish/stockfish.exe"
THREADS = int(cfg.get("ENGINE_THREADS", 2))
HASH_MB = int(cfg.get("ENGINE_HASH_MB", 256))

app = FastAPI(title="DeepChessIQ Engine Service")

sf = None  # sf will hold the Stockfish process.
init_error: str | None = None
sf_lock = (
    threading.Lock()
)  # sf_lock makes access thread-safe (FastAPI can handle multiple requests at once).


def _init_engine():
    global sf, init_error
    try:
        if not Path(ENGINE_PATH).exists():  #
            init_error = f"ENGINE_PATH not found: {ENGINE_PATH}"
            sf = None
            return

        engine = Stockfish(
            path=ENGINE_PATH,
            parameters={"Threads": THREADS, "Hash": HASH_MB},
        )
        # Don't call is_ready() (not present in some versions). We'll probe in /health.
        sf = engine
        init_error = None
    except Exception as e:
        init_error = str(e)
        sf = None


_init_engine()


class BestMoveReq(BaseModel):
    fen: str
    movetime: int | None = 200  # ms


# Routes for the FastAPI application.
@app.get("/ping")
def ping():
    return {"ok": True}  # Simple liveness probe.


# Info about the engine and its status: shows what engine path & settings the service is using and whether init succeeded.
@app.get("/info")
def info():
    return {
        "engine_path": ENGINE_PATH,
        "threads": THREADS,
        "hash_mb": HASH_MB,
        "initialized": sf is not None,
        "init_error": init_error,
    }


# Health probe: tries a quick move from the starting position to verify the engine is responsive.
# If we get a UCI move back, we’re good.
@app.get("/health")
def health():
    """
    Health probe without using is_ready():
    Try a 10ms move from the start position. If it returns a UCI move, engine is healthy.
    """
    if sf is None:
        return {"ready": False, "error": init_error or "Stockfish not initialized"}

    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    try:
        with sf_lock:
            sf.set_fen_position(start_fen)
            m = sf.get_best_move_time(10)  # tiny think time
        return {"ready": bool(m), "probe_move": m}
    except Exception as e:
        return {"ready": False, "error": str(e)}


def _validate_fen(fen: str):
    if HAVE_CHESS:
        try:
            chess.Board(fen=fen)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid FEN position")
    else:
        try:
            if hasattr(sf, "is_fen_valid") and not sf.is_fen_valid(fen):
                raise HTTPException(status_code=400, detail="Invalid FEN position")
        except Exception:
            pass


def _get_move_and_info(fen: str, movetime: int | None):
    with sf_lock:
        sf.set_fen_position(fen)
        move = sf.get_best_move_time(movetime) if movetime else sf.get_best_move()
        if move is None:
            raise HTTPException(
                status_code=400, detail="No valid moves available from this position"
            )
        evaluation = sf.get_evaluation() if hasattr(sf, "get_evaluation") else None
        top_moves = sf.get_top_moves(1) if hasattr(sf, "get_top_moves") else []
    return move, evaluation, top_moves


# Endpoint to get the best move from a given FEN position within an optional movetime.
@app.post("/bestmove")
def bestmove(req: BestMoveReq):
    if sf is None:
        raise HTTPException(
            status_code=503, detail=init_error or "Stockfish not available"
        )

    _validate_fen(req.fen)

    try:
        move, evaluation, top_moves = _get_move_and_info(req.fen, req.movetime)
        return {"uci": move, "eval": evaluation, "pv": top_moves}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")
