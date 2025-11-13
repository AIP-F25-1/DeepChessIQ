import os
from pathlib import Path
from typing import List, Dict, Any

import chess
import chess.engine
from dotenv import load_dotenv

load_dotenv()

ENGINE_PATH = 'E:\Projects\AIP\stockfish\stockfish-windows-x86-64-avx2.exe'
ENGINE_THREADS = int(os.getenv("ENGINE_THREADS", "2"))
ENGINE_HASH_MB = int(os.getenv("ENGINE_HASH_MB", "512"))

ENGINE_LIMIT_MODE = os.getenv("ENGINE_LIMIT_MODE", "movetime").lower()  # "movetime" | "depth"
ENGINE_MOVETIME_MS = int(os.getenv("ENGINE_MOVETIME_MS", "300"))
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "14"))

SHORTLIST_N = int(os.getenv("SHORTLIST_N", "20"))

def _limit() -> chess.engine.Limit:
    if ENGINE_LIMIT_MODE == "depth":
        return chess.engine.Limit(depth=ENGINE_DEPTH)
    return chess.engine.Limit(time=ENGINE_MOVETIME_MS / 1000.0)

def _score_fields(score: chess.engine.PovScore) -> Dict[str, Any]:
    if score.is_mate():
        return {"score_cp": None, "mate": int(score.mate())}
    cp = score.score()
    return {"score_cp": int(cp) if cp is not None else None, "mate": None}

class StockfishService:
    def __init__(self):
        self.engine = None

    def open(self):
        import shutil
        exe = ENGINE_PATH
        candidate = exe if Path(exe).exists() else shutil.which(exe)
        if not candidate or not Path(candidate).exists():
            raise FileNotFoundError(
                f"Could not locate Stockfish. Set ENGINE_PATH to a valid full path. Current ENGINE_PATH={ENGINE_PATH!r}"
            )
        self.engine = chess.engine.SimpleEngine.popen_uci(candidate)
        for k, v in (("Threads", ENGINE_THREADS), ("Hash", ENGINE_HASH_MB)):
            try: self.engine.configure({k: v})
            except Exception: pass
        for opt in ("Use NNUE", "UCI_AnalyseMode"):
            try: self.engine.configure({opt: True})
            except Exception: pass

    def close(self):
        if self.engine is not None:
            try: self.engine.quit()
            finally: self.engine = None

    def __enter__(self): self.open(); return self
    def __exit__(self, exc_type, exc, tb): self.close()

    def get_top_moves(self, fen: str, n: int = SHORTLIST_N) -> Dict[str, Any]:
        if self.engine is None:
            raise RuntimeError("Engine is not open. Use context manager or call open().")
        board = chess.Board(fen)
        legal_count = board.legal_moves.count()
        k = min(max(1, n), max(1, legal_count))
        info_list: List[chess.engine.InfoDict] = self.engine.analyse(board, limit=_limit(), multipv=k)

        def info_key(info: chess.engine.InfoDict):
            score = info["score"].pov(board.turn)
            if score.is_mate():
                # higher positive mate is better; negative is worse
                return (1, score.mate())
            return (0, score.score() if score.score() is not None else -10**9)

        top_moves = []
        for info in sorted(info_list, key=info_key, reverse=True):
            pv = info.get("pv", [])
            if not pv: continue
            first = pv[0]
            if first not in board.legal_moves: continue
            pov = info["score"].pov(board.turn)
            sf = _score_fields(pov)
            top_moves.append({
                "uci": first.uci(),
                "score_cp": sf["score_cp"],
                "mate": sf["mate"],
                "depth": int(info.get("depth", 0)) or None,
                "pv": " ".join(m.uci() for m in pv)
            })

        return {
            "fen": fen,
            "top_moves": top_moves[:k],
            "meta": {
                "engine_name": "Stockfish",
                "threads": ENGINE_THREADS,
                "hash_mb": ENGINE_HASH_MB,
                "limit": ({"movetime_ms": ENGINE_MOVETIME_MS} if ENGINE_LIMIT_MODE=="movetime" else {"depth": ENGINE_DEPTH})
            }
        }
