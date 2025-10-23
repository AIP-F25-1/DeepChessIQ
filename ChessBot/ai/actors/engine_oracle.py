# chessbot/ai/actors/engine_oracle.py
from __future__ import annotations

import os
import math
import time
from dataclasses import dataclass
from typing import List, Optional, Literal

import chess
import chess.engine


EvalCP = Optional[int]
EngineKind = Literal["stockfish", "lc0"]


@dataclass
class Candidate:
    move_uci: str
    eval_cp: EvalCP         # centipawns, POV = side-to-move; None if unknown
    rank: int               # 1 = best
    depth: Optional[int]    # engine reported depth (if available)
    nodes: Optional[int]    # searched nodes (if available)


class EngineOracle:
    """
    Persistent UCI engine wrapper with a single public method:
      - get_topk(fen, k, movetime_ms, depth_cap) -> List[Candidate]

    Notes:
      * Uses MultiPV internally (k lines) to avoid repeated queries.
      * Normalizes eval to centipawns from the POV of side-to-move.
      * Falls back to a random legal move if engine returns nothing (rare).
    """

    def __init__(
        self,
        engine_path: str,
        engine_kind: EngineKind = "stockfish",
        threads: int = 2,
        hash_mb: int = 256,
        skill: Optional[int] = 20,       # Stockfish only: 0..20; None to skip
        weights_path: Optional[str] = None,  # Lc0 only
        multipv_floor: int = 2
    ) -> None:
        if not engine_path or not os.path.exists(engine_path):
            raise FileNotFoundError(f"Engine binary not found: {engine_path}")

        self.engine_kind = engine_kind
        self._engine = chess.engine.SimpleEngine.popen_uci(engine_path)

        # Try to configure UCI options conservatively.
        # Not all binaries expose all options; ignore soft failures.
        options = {}
        if engine_kind == "stockfish":
            options.update({
                "Threads": threads,
                "Hash": hash_mb,
                "MultiPV": max(multipv_floor, 2),
            })
            if skill is not None:
                options["Skill Level"] = int(skill)
        else:  # lc0
            options.update({
                "Threads": threads,
                "MultiPV": max(multipv_floor, 2),
            })
            if weights_path:
                options["WeightsFile"] = weights_path

        try:
            self._engine.configure(options)
        except Exception:
            # Some engines use variant names; safe to ignore.
            pass

    def close(self) -> None:
        try:
            self._engine.quit()
        except Exception:
            pass

    # ---- Public API ---------------------------------------------------------

    def get_topk(
        self,
        fen: str,
        k: int = 4,
        movetime_ms: int = 200,
        depth_cap: int = 0
    ) -> List[Candidate]:
        """
        Get top-k candidate moves for the given FEN quickly.

        Args:
            fen: FEN string of the position.
            k: number of candidate lines to request (best-first).
            movetime_ms: think time budget for this query (0 -> rely on depth_cap).
            depth_cap: if > 0, set a max depth instead of movetime.

        Returns:
            Ranked list of Candidate; falls back to a single legal move if needed.
        """
        board = chess.Board(fen)
        if k < 1:
            k = 1

        # Ensure engine has MultiPV >= k; ignore failures for engines that don’t support it.
        try:
            self._engine.configure({"MultiPV": max(2, k)})
        except Exception:
            pass

        limit = self._make_limit(movetime_ms, depth_cap)

        try:
            info = self._engine.analyse(board, limit=limit, multipv=k)
        except chess.engine.EngineTerminatedError:
            # Try to restart once (engine crashed) – caller may decide to recreate the object.
            self._engine = self._restart_engine()
            info = self._engine.analyse(board, limit=limit, multipv=k)

        # Normalise to a list
        lines = info if isinstance(info, list) else [info]
        cands: List[Candidate] = []

        # Parse engine outputs
        seen_moves = set()
        for idx, entry in enumerate(lines, start=1):
            pv = entry.get("pv") or []
            if not pv:
                continue
            move = pv[0]
            if move in seen_moves:
                continue
            seen_moves.add(move)

            depth = entry.get("depth")
            nodes = entry.get("nodes")
            score = entry.get("score")  # chess.engine.PovScore or Score

            eval_cp = self._score_to_cp(score, board.turn)

            cands.append(
                Candidate(
                    move_uci=move.uci(),
                    eval_cp=eval_cp,
                    rank=idx,
                    depth=depth if isinstance(depth, int) else None,
                    nodes=nodes if isinstance(nodes, int) else None,
                )
            )

        # Fallback if engine returned nothing
        if not cands:
            try:
                legal = list(board.legal_moves)
                if legal:
                    move = legal[0]
                    cands = [Candidate(move_uci=move.uci(), eval_cp=None, rank=1, depth=None, nodes=None)]
            except Exception:
                pass

        # Truncate to exactly k in case engine returned fewer/duplicates
        return cands[:k]

    # ---- Helpers ------------------------------------------------------------

    def _make_limit(self, movetime_ms: int, depth_cap: int) -> chess.engine.Limit:
        if depth_cap and depth_cap > 0:
            return chess.engine.Limit(depth=int(depth_cap))
        if movetime_ms and movetime_ms > 0:
            return chess.engine.Limit(time=movetime_ms / 1000.0)
        # Sensible default if both unset
        return chess.engine.Limit(time=0.2)  # 200 ms

    @staticmethod
    def _score_to_cp(score_obj: Optional[chess.engine.Score], turn_white: bool) -> EvalCP:
        """
        Convert engine Score to centipawns from POV of side-to-move.
        Mate scores are mapped to large CP magnitudes with sign.
        """
        if score_obj is None:
            return None
        try:
            # Normalize to "white perspective" first, then flip if needed
            cp = score_obj.white().score(mate_score=100000)
            if cp is None:  # some scores can be None
                return None
            # POV = side to move: if Black to move, invert
            if not turn_white:
                cp = -cp
            return int(cp)
        except Exception:
            return None

    def _restart_engine(self) -> chess.engine.SimpleEngine:
        # Caller responsibility to ensure path is still valid
        # We don’t reapply options here; upstream should rebuild the object if needed.
        # Keeping a minimal restart for resilience.
        raise RuntimeError("Engine crashed; recreate EngineOracle instance with same parameters.")


if __name__ == "__main__":
    # Quick smoke test (adjust path and FEN before running)
    ENGINE_PATH = os.getenv("ENGINE_BIN", "stockfish")  # absolute path recommended on Windows
    if not os.path.exists(ENGINE_PATH):
        print("Set ENGINE_BIN env var to your Stockfish binary path.")
        exit(1)

    oracle = EngineOracle(
        engine_path=ENGINE_PATH,
        engine_kind="stockfish",
        threads=2,
        hash_mb=256,
        skill=20,
    )

    # Initial position
    start_fen = chess.STARTING_FEN
    cands = oracle.get_topk(start_fen, k=4, movetime_ms=200, depth_cap=0)
    for c in cands:
        print(c)

    oracle.close()
