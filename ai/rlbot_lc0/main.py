import os
import uuid
import json
import logging
import pathlib
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import chess
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import dotenv_values
from uci_runner import Lc0Runner
from persona import choose_move

# Load .env safely with defaults
cfg = {**dotenv_values(str(pathlib.Path(__file__).with_name(".env"))), **os.environ}

LC0_BIN = cfg.get("LC0_BIN")
RL_NET_PATH = cfg.get("RL_NET_PATH")
RL_THREADS = int(cfg.get("RL_THREADS", 2))
RL_MOVETIME_MS = int(cfg.get("RL_MOVETIME_MS", 200))
CORS_ORIGIN = cfg.get("CORS_ORIGIN", "http://localhost:3000")
MODEL_REGISTRY_PATH = cfg.get(
    "MODEL_REGISTRY", str(pathlib.Path(__file__).with_name("model_registry.json"))
)

# Convert relative paths to absolute
if LC0_BIN and not os.path.isabs(LC0_BIN):
    LC0_BIN = str(pathlib.Path(__file__).parent.parent.parent / LC0_BIN)
if RL_NET_PATH and not os.path.isabs(RL_NET_PATH):
    RL_NET_PATH = str(pathlib.Path(__file__).parent.parent.parent / RL_NET_PATH)

missing_critical = not LC0_BIN or not RL_NET_PATH

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engine
engine_runner = Lc0Runner()

# Model registry
try:
    with open(MODEL_REGISTRY_PATH, "r") as f:
        model_registry = json.load(f)
except FileNotFoundError:
    model_registry = {"models": {}}

# Session storage (in-memory for simplicity)
sessions: Dict[str, Dict[str, Any]] = {}


class MoveRequest(BaseModel):
    uci: str


class BestMoveRequest(BaseModel):
    fen: str
    movetime_ms: Optional[int] = 200


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not missing_critical:
        engine_runner.start(LC0_BIN, RL_NET_PATH, RL_THREADS)
        # Warm-up
        board = chess.Board()
        engine_runner.bestmove(board.fen(), 50)
        logger.info("Lc0 engine started and warmed up")
    else:
        logger.warning("Missing LC0_BIN or RL_NET_PATH, engine not started")
    yield
    # Shutdown
    if not missing_critical:
        engine_runner.shutdown()
        logger.info("Lc0 engine shut down")


app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"ok": True}


@app.get("/health")
def health():
    if missing_critical:
        return {"ready": False, "detail": "Missing LC0_BIN or RL_NET_PATH in .env"}
    if not engine_runner.isready():
        return {"ready": False, "detail": "Engine not ready"}
    # Quick probe
    try:
        result = engine_runner.bestmove(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 10
        )
        probe = result["best"]["uci"]
        return {
            "ready": True,
            "probe": probe,
            "backend": engine_runner.backend,
            "threads": RL_THREADS,
        }
    except Exception as e:
        return {"ready": False, "detail": str(e)}


@app.post("/session")
def create_session(
    engine: str = Query(..., description="Engine type, must be 'rl'"),
    bot_id: Optional[str] = None,
    temperature: Optional[float] = None,
    mistake_rate: Optional[float] = None,
    blunder_cap_cp: Optional[int] = None,
    movetime_ms: Optional[int] = None,
):
    if engine != "rl":
        raise HTTPException(status_code=400, detail="Only 'rl' engine supported")
    if bot_id and bot_id not in model_registry["models"]:
        logger.warning(f"Unknown bot_id: {bot_id}")
        raise HTTPException(status_code=400, detail=f"Unknown bot_id: {bot_id}")
    session_id = str(uuid.uuid4())
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    turn = "w"
    history = []
    persona = {
        "temperature": temperature or float(os.getenv("PERSONA_TEMPERATURE", 0.3)),
        "mistake_rate": mistake_rate or float(os.getenv("PERSONA_MISTAKE_RATE", 0.03)),
        "blunder_cap_cp": blunder_cap_cp
        or int(os.getenv("PERSONA_BLUNDER_CAP_CP", 300)),
        "movetime_ms": movetime_ms or int(os.getenv("RL_MOVETIME_MS", 200)),
    }
    # Select net
    net_path = RL_NET_PATH
    if bot_id:
        net_path = model_registry["models"][bot_id]
        logger.info(f"Switching to bot {bot_id} with net {net_path}")
        engine_runner.set_weights(net_path)
    sessions[session_id] = {
        "fen": fen,
        "turn": turn,
        "history": history,
        "persona": persona,
        "board": chess.Board(fen),
    }
    return {
        "session_id": session_id,
        "fen": fen,
        "turn": turn,
        "history": history,
    }


@app.post("/session/{session_id}/move")
def make_move(session_id: str, move_req: MoveRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    if missing_critical:
        raise HTTPException(
            status_code=503, detail="engine not initialized (check .env paths)"
        )
    session = sessions[session_id]
    board = session["board"]
    try:
        move = chess.Move.from_uci(move_req.uci)
        if move not in board.legal_moves:
            raise HTTPException(status_code=400, detail="Illegal move")
        board.push(move)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UCI")
    session["fen"] = board.fen()
    session["turn"] = "w" if board.turn else "b"
    user_move = move_req.uci
    # Bot move if not terminal
    bot_move = None
    candidates = []
    elapsed_ms = 0
    if not board.is_game_over() and not board.turn:  # Bot is black
        try:
            result = engine_runner.bestmove(
                board.fen(), session["persona"]["movetime_ms"]
            )
            candidates = result["candidates"]
            chosen_uci = choose_move(
                candidates,
                session["persona"]["temperature"],
                session["persona"]["mistake_rate"],
                session["persona"]["blunder_cap_cp"],
            )
            move = chess.Move.from_uci(chosen_uci)
            board.push(move)
            bot_move = chosen_uci
            elapsed_ms = result["elapsed_ms"]
            session["fen"] = board.fen()
            session["turn"] = "w"
        except Exception as e:
            logger.error(f"Bot move failed: {e}")
            raise HTTPException(status_code=503, detail="Engine error")
    session["history"].append(
        {
            "user_move": user_move,
            "bot_move": bot_move,
            "elapsed_ms": elapsed_ms,
            "candidates": candidates,
        }
    )
    return {
        "fen": session["fen"],
        "turn": session["turn"],
        "history": session["history"],
        "used": {
            "movetime_ms": session["persona"]["movetime_ms"],
            "backend": result.get("backend", "cpu") if "result" in locals() else "cpu",
        },
    }


@app.post("/session/{session_id}/resign")
def resign(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    board = session["board"]
    if board.is_game_over():
        result = "1/2-1/2"
    elif board.turn:  # White to move, resign means black wins
        result = "0-1"
    else:
        result = "1-0"
    del sessions[session_id]
    return {"result": result}


@app.post("/bestmove")
def bestmove(req: BestMoveRequest):
    if missing_critical:
        raise HTTPException(
            status_code=503, detail="engine not initialized (check .env paths)"
        )
    try:
        result = engine_runner.bestmove(req.fen, req.movetime_ms or 200)
        return {
            "uci": result["best"]["uci"],
            "used": {"movetime_ms": req.movetime_ms or 200},
            "candidates": result["candidates"],
        }
    except chess.InvalidBoardError:
        raise HTTPException(status_code=400, detail="Invalid FEN")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
