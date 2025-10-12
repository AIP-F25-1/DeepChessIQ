import os
import threading
from pathlib import Path
from time import perf_counter
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import dotenv_values
from stockfish import Stockfish

# Optional: robust FEN validation if python-chess is installed
try:
    import chess

    HAVE_CHESS = True
except Exception:
    HAVE_CHESS = False

# --- config ---
cfg = {**dotenv_values(".env"), **os.environ}
ENGINE_PATH = cfg.get("ENGINE_PATH") or "ai/tools/stockfish/stockfish.exe"
THREADS = int(cfg.get("ENGINE_THREADS", 2))
HASH_MB = int(cfg.get("ENGINE_HASH_MB", 256))
CORS_ALLOW_ORIGINS = [
    # Add your FE origin(s) here in prod, e.g. "http://localhost:5173", "https://your.site"
    cfg.get("CORS_ORIGIN", "http://localhost:3000")
]

app = FastAPI(title="DeepChessIQ Engine Service")

# CORS so the frontend can call the API directly (if you choose not to proxy via Node)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sf = None
init_error: str | None = None
sf_lock = threading.Lock()  # the stockfish wrapper is not thread-safe


def _init_engine():
    """Initialize a single Stockfish process."""
    global sf, init_error
    try:
        if not Path(ENGINE_PATH).exists():
            init_error = f"ENGINE_PATH not found: {ENGINE_PATH}"
            sf = None
            return

        engine = Stockfish(
            path=ENGINE_PATH,
            parameters={"Threads": THREADS, "Hash": HASH_MB},
        )
        # Some wrapper versions don't implement is_ready(); we probe in /health instead.
        sf = engine
        init_error = None
    except Exception as e:
        init_error = str(e)
        sf = None


_init_engine()


# --- models ---
class BestMoveReq(BaseModel):
    fen: str
    movetime: Optional[int] = None  # ms (explicit time mode)
    depth: Optional[int] = None  # plies (explicit depth mode)


# --- routes ---
@app.get("/ping")
def ping():
    return {"ok": True}


@app.get("/version")
def version():
    return {
        "engine_path": ENGINE_PATH,
        "threads": THREADS,
        "hash_mb": HASH_MB,
        "wrapper_module": getattr(Stockfish, "__module__", "stockfish"),
        "initialized": sf is not None,
        "init_error": init_error,
    }


@app.get("/health")
def health():
    """Health probe: try a tiny (10ms) move from startpos."""
    if sf is None:
        return {"ready": False, "error": init_error or "Stockfish not initialized"}
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    try:
        with sf_lock:
            sf.set_fen_position(start_fen)
            m = sf.get_best_move_time(10)
        return {"ready": bool(m), "probe_move": m}
    except Exception as e:
        return {"ready": False, "error": str(e)}


def _validate_fen(fen: str):
    if not fen or not isinstance(fen, str):
        raise HTTPException(status_code=400, detail="FEN is required")
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
            # If validation API not available, let engine fail downstream.
            pass


# --- helper ---
def _search_bestmove(fen: str, movetime: Optional[int], depth: Optional[int]):
    """Run Stockfish either in time-mode (movetime ms) or depth-mode (plies)."""
    if sf is None:
        raise HTTPException(
            status_code=503, detail=init_error or "Stockfish not available"
        )

    _validate_fen(fen)

    with sf_lock:
        sf.set_fen_position(fen)
        t0 = perf_counter()

        # Priority: explicit depth > explicit movetime > defaults from .env (optional)
        if depth is not None and hasattr(sf, "set_depth"):
            sf.set_depth(int(depth))
            uci = sf.get_best_move()
            mode_used = {"mode": "depth", "depth": int(depth)}
        elif movetime is not None:
            uci = sf.get_best_move_time(int(movetime))
            mode_used = {"mode": "time", "movetime": int(movetime)}
        else:
            # Fallback default: behave like quick interactive time-mode if neither provided
            uci = sf.get_best_move_time(200)
            mode_used = {"mode": "time", "movetime": 200}

        elapsed_ms = int((perf_counter() - t0) * 1000)

        if uci is None:
            raise HTTPException(
                status_code=400, detail="No valid moves available from this position"
            )

        evaluation = sf.get_evaluation() if hasattr(sf, "get_evaluation") else None
        pv = sf.get_top_moves(1) if hasattr(sf, "get_top_moves") else []

    # If time-mode, provide an approximate depth estimate (for UI/debug)
    if mode_used["mode"] == "time":
        approx_depth = int(12 + (mode_used["movetime"] / 100) * 1.5)
        mode_used["approx_depth"] = approx_depth

    mode_used["elapsed_ms"] = elapsed_ms
    return {"uci": uci, "eval": evaluation, "pv": pv, "used": mode_used}


# --- endpoint ---
@app.post("/bestmove")
def bestmove(req: BestMoveReq):
    try:
        return _search_bestmove(req.fen, req.movetime, req.depth)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")
