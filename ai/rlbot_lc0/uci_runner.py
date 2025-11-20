import subprocess
import threading
import time
import re
from typing import Optional, List, Dict, Any
import chess.engine


def _score_to_cp(s) -> int:
    if s is None:
        return 0
    try:
        return s.cp  # Cp or PovScore(Cp)
    except Exception:
        try:
            m = s.mate()  # Mate or PovScore(Mate)
            if m is None:
                return 0
            return 32767 if m > 0 else -32767
        except Exception:
            return 0


class Lc0Runner:
    def __init__(self):
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.lock = threading.Lock()
        self.backend: Optional[str] = None

    def start(
        self,
        lc0_bin: str,
        weights_path: str,
        threads: int,
        backend_opts: Optional[Dict[str, Any]] = None,
    ):
        with self.lock:
            if self.engine:
                self.engine.quit()
            self.engine = chess.engine.SimpleEngine.popen_uci(lc0_bin)
            self.engine.configure({"WeightsFile": weights_path, "Threads": threads})
            if backend_opts:
                self.engine.configure(backend_opts)
            # Detect backend from info lines
            self.backend = self._detect_backend()
            # Warm-up
            board = chess.Board()
            self.engine.play(board, chess.engine.Limit(time=0.05))

    def _detect_backend(self) -> str:
        for candidate in ("cuda", "opencl", "cpu"):
            try:
                self.engine.configure({"Backend": candidate})
                return candidate
            except Exception:
                continue
        return "cpu"

    def set_weights(self, weights_path: str):
        with self.lock:
            if self.engine:
                self.engine.configure({"WeightsFile": weights_path})

    def set_threads(self, threads: int):
        with self.lock:
            if self.engine:
                self.engine.configure({"Threads": threads})

    def isready(self) -> bool:
        with self.lock:
            if not self.engine:
                return False
            try:
                self.engine.ping()
                return True
            except:
                return False

    def bestmove(self, fen: str, movetime_ms: int, multipv: int = 3) -> Dict[str, Any]:
        with self.lock:
            if not self.engine:
                raise RuntimeError("Engine not started")
            board = chess.Board(fen)
            start_time = time.time()
            limit = chess.engine.Limit(time=movetime_ms / 1000.0)
            try:
                result = self.engine.analyse(board, limit, multipv=multipv)
            except Exception as e:
                raise RuntimeError(f"Engine analysis failed: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            # Parse result
            if isinstance(result, list):
                # MultiPV
                candidates = []
                for pv in result:
                    move = pv["pv"][0] if pv["pv"] else None
                    cp = _score_to_cp(pv.get("score"))
                    uci = move.uci() if move else ""
                    if uci:  # Filter empty PV entries
                        candidates.append({"uci": uci, "cp": cp})
                best = candidates[0] if candidates else {"uci": ""}
            else:
                # Single
                move = result["pv"][0] if result["pv"] else None
                cp = _score_to_cp(result.get("score"))
                uci = move.uci() if move else ""
                best = {"uci": uci}
                candidates = [{"uci": uci, "cp": cp}] if uci else []
            return {
                "best": best,
                "candidates": candidates,
                "elapsed_ms": elapsed_ms,
                "backend": self.backend or "cpu",
            }

    def shutdown(self):
        with self.lock:
            if self.engine:
                self.engine.quit()
                self.engine = None
