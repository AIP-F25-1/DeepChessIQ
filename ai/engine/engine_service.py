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
    movetime: Optional[int] = None  # ms; time-based mode
    depth: Optional[int] = None  # plies; fixed-depth mode


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


@app.post("/bestmove")
def bestmove(req: BestMoveReq):
    if sf is None:
        raise HTTPException(
            status_code=503, detail=init_error or "Stockfish not available"
        )

    _validate_fen(req.fen)

    # Force fixed movetime mode for consistency (200ms per move)
    req.movetime = 200
    req.depth = None  # ignore depth if both provided

    try:
        with sf_lock:
            sf.set_fen_position(req.fen)
            t0 = perf_counter()

            # Always use movetime=200 for time-based search
            move = sf.get_best_move_time(req.movetime)
            used = {"mode": "time", "movetime": req.movetime}

            elapsed_ms = int((perf_counter() - t0) * 1000)

            if move is None:
                raise HTTPException(
                    status_code=400,
                    detail="No valid moves available from this position",
                )

            # Optional infos (wrapper-dependent)
            evaluation = sf.get_evaluation() if hasattr(sf, "get_evaluation") else None
            top_moves = sf.get_top_moves(1) if hasattr(sf, "get_top_moves") else []

        # Optionally estimate search depth based on movetime (rough heuristic)
        approx_depth = int(12 + (req.movetime / 100) * 1.5)
        used["elapsed_ms"] = elapsed_ms
        used["approx_depth"] = approx_depth

        return {"uci": move, "eval": evaluation, "pv": top_moves, "used": used}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine error: {e}")
