# env_chess_rllib.py
from __future__ import annotations
import os, math, random
from typing import Dict, Tuple, List, Optional

import gym
import numpy as np
import chess
import chess.pgn

try:
    # Optional: if you already saved the earlier EngineOracle class, you can use it
    from chessbot.ai.actors.engine_oracle import EngineOracle
except Exception:
    EngineOracle = None  # We'll use a mock fallback


# ---------- Move encoding (fixed 4672 space; AlphaZero-style) ----------

# Map (from_square, to_square, promo_piece_idx) into [0..4671]
# promo_piece_idx: 0=None, 1=Knight, 2=Bishop, 3=Rook, 4=Queen  (5 options)
# 64 * 73 = 4672 in most AZ impls, but here we use a compact 64*64*5 -> 20480 and remap smaller.
# For simplicity, we use a common 4672 mapping: 64 origins * 73 targets/flags (Ray examples).
# To keep it practical, we’ll implement a compact, deterministic mapping:
#   index = from_sq* (64*5) + to_sq*5 + promo_idx   (max 64*64*5 = 20480)
# Then we will mask illegal indices; policy learns with the mask.
# We’ll keep ACTION_SPACE_SIZE = 20480 (safe upper bound) for simplicity.

ACTION_SPACE_SIZE = 20480
PROMO_NONE, PROMO_N, PROMO_B, PROMO_R, PROMO_Q = 0, 1, 2, 3, 4

def move_to_index(m: chess.Move) -> int:
    promo_idx = PROMO_NONE
    if m.promotion:
        promo_idx = {chess.KNIGHT: PROMO_N, chess.BISHOP: PROMO_B, chess.ROOK: PROMO_R, chess.QUEEN: PROMO_Q}[m.promotion]
    return m.from_square * (64*5) + m.to_square * 5 + promo_idx

def index_to_move(idx: int, board: chess.Board) -> Optional[chess.Move]:
    from_sq = idx // (64*5)
    rest = idx % (64*5)
    to_sq = rest // 5
    promo_idx = rest % 5
    promo_map = {PROMO_NONE: None, PROMO_N: chess.KNIGHT, PROMO_B: chess.BISHOP, PROMO_R: chess.ROOK, PROMO_Q: chess.QUEEN}
    mv = chess.Move(from_sq, to_sq, promotion=promo_map[promo_idx])
    return mv if mv in board.legal_moves else None


# ---------- Observation builder ----------
# Simple, fast features: 12 piece planes + side-to-move + castling + ep flag + material counts
OBS_SIZE = 12*64 + 6 + 2  # 12 planes + 6 material buckets + 2 flags

def board_to_obs(board: chess.Board) -> np.ndarray:
    planes = np.zeros((12, 64), dtype=np.float32)
    piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
    for color in [chess.WHITE, chess.BLACK]:
        base = 0 if color == chess.WHITE else 6
        for i, pt in enumerate(piece_types):
            for sq in board.pieces(pt, color):
                planes[base + i, sq] = 1.0
    planes = planes.reshape(-1)

    # Simple extras
    side = np.array([1.0 if board.turn == chess.WHITE else 0.0], dtype=np.float32)
    castling = np.array([
        1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0,
        1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0,
        1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0,
        1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0,
    ], dtype=np.float32)
    ep = np.array([1.0 if board.ep_square is not None else 0.0], dtype=np.float32)

    # Material counts (very coarse)
    mat = np.array([
        len(board.pieces(chess.PAWN, chess.WHITE)) - len(board.pieces(chess.PAWN, chess.BLACK)),
        len(board.pieces(chess.KNIGHT, chess.WHITE)) - len(board.pieces(chess.KNIGHT, chess.BLACK)),
        len(board.pieces(chess.BISHOP, chess.WHITE)) - len(board.pieces(chess.BISHOP, chess.BLACK)),
        len(board.pieces(chess.ROOK, chess.WHITE)) - len(board.pieces(chess.ROOK, chess.BLACK)),
        len(board.pieces(chess.QUEEN, chess.WHITE)) - len(board.pieces(chess.QUEEN, chess.BLACK)),
        len(board.pieces(chess.KING, chess.WHITE)) - len(board.pieces(chess.KING, chess.BLACK)),
    ], dtype=np.float32)

    return np.concatenate([planes, side, castling, ep, mat], axis=0)


def legal_action_mask(board: chess.Board) -> np.ndarray:
    mask = np.zeros((ACTION_SPACE_SIZE,), dtype=np.float32)
    for m in board.legal_moves:
        mask[move_to_index(m)] = 1.0
    return mask


# ---------- Engine adapter ----------
class MockEngine:
    """Fallback opponent: chooses a legal move with a bit of material-aware bias."""
    PIECE_VALUES = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
    }
    def pick_move(self, board: chess.Board) -> chess.Move:
        moves = list(board.legal_moves)
        if not moves:
            raise RuntimeError("No legal moves")
        # score capture moves higher; otherwise random
        scored = []
        for m in moves:
            score = 0
            if board.is_capture(m):
                cap_sq = m.to_square
                if board.is_en_passant(m):
                    score += 100
                else:
                    piece = board.piece_at(cap_sq)
                    if piece:
                        score += self.PIECE_VALUES.get(piece.piece_type, 0)
            if board.gives_check(m):
                score += 25
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for s, m in scored[:5]] if len(scored) >= 5 else [m for s, m in scored]
        return random.choice(top)


class EngineAdapter:
    """Wraps real EngineOracle if available, else MockEngine."""
    def __init__(self, use_mock: bool = False, engine_bin: Optional[str] = None):
        self.use_mock = use_mock or (EngineOracle is None) or (not engine_bin) or (not os.path.exists(engine_bin))
        self.mock = MockEngine() if self.use_mock else None
        self.oracle = None
        if not self.use_mock:
            self.oracle = EngineOracle(engine_path=engine_bin, engine_kind="stockfish", threads=2, hash_mb=256, skill=20)

    def pick_move(self, board: chess.Board, k: int = 4, movetime_ms: int = 120, depth_cap: int = 0) -> chess.Move:
        if self.use_mock:
            return self.mock.pick_move(board)
        cands = self.oracle.get_topk(board.fen(), k=k, movetime_ms=movetime_ms, depth_cap=depth_cap)
        if not cands:
            return self.mock.pick_move(board)
        # sample among top-k a bit to be less brittle
        top = cands[:min(k, len(cands))]
        # bias to best but allow a bit of variety
        weights = np.array([1.0/(i.rank) for i in top], dtype=np.float32)
        weights = weights / weights.sum()
        idx = np.random.choice(len(top), p=weights)
        return chess.Move.from_uci(top[idx].move_uci)

    def close(self):
        try:
            if self.oracle:
                self.oracle.close()
        except Exception:
            pass


# ---------- The RLlib Env ----------
class ChessVsEngineEnv(gym.Env):
    """
    Single-agent environment.
    Agent plays WHITE by default; the opponent (engine) plays BLACK.
    Each step applies the agent's move; env then (if game not over) applies the engine move.
    Reward: +1/-1/0 at terminal; optional tiny eval shaping could be added later.
    """
    metadata = {"render.modes": ["ansi"]}

    def __init__(self, config: Dict = None):
        config = config or {}
        self.agent_color_white = config.get("agent_plays_white", True)
        self.engine_k = int(config.get("engine_k", 4))
        self.movetime_ms = int(config.get("movetime_ms", 120))
        self.depth_cap = int(config.get("depth_cap", 0))
        self.use_mock_engine = bool(config.get("use_mock_engine", True))
        self.engine_bin = config.get("engine_bin")

        self.engine = EngineAdapter(self.use_mock_engine, self.engine_bin)

        # RLlib expects Dict obs for action masking: {"obs": vec, "action_mask": mask}
        self.observation_space = gym.spaces.Dict({
            "obs": gym.spaces.Box(low=0.0, high=1.0, shape=(OBS_SIZE,), dtype=np.float32),
            "action_mask": gym.spaces.Box(low=0, high=1, shape=(ACTION_SPACE_SIZE,), dtype=np.float32),
        })
        self.action_space = gym.spaces.Discrete(ACTION_SPACE_SIZE)

        self.board = chess.Board()
        self.done = False

        # If agent plays black, let engine move first at reset
        self._pending_engine_move_after_reset = not self.agent_color_white

    # ---- Gym API ----
    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict] = None):
        super().reset(seed=seed)
        self.board = chess.Board()
        self.done = False
        self._pending_engine_move_after_reset = not self.agent_color_white

        if self._pending_engine_move_after_reset and not self.board.is_game_over():
            eng_move = self.engine.pick_move(self.board, k=self.engine_k, movetime_ms=self.movetime_ms, depth_cap=self.depth_cap)
            self.board.push(eng_move)

        return self._obs(), {}

    def step(self, action: int):
        if self.done:
            return self._obs(), 0.0, True, False, {}

        # Agent move
        move = index_to_move(int(action), self.board)
        if (move is None) or (move not in self.board.legal_moves):
            # Illegal action: small negative reward and skip turn (or terminate)
            # Here we terminate with large penalty to encourage respecting mask
            self.done = True
            return self._obs(), -1.0, True, False, {"illegal_action": True}

        self.board.push(move)
        if self.board.is_game_over():
            r = self._terminal_reward()
            self.done = True
            return self._obs(), r, True, False, {}

        # Engine move
        eng_move = self.engine.pick_move(self.board, k=self.engine_k, movetime_ms=self.movetime_ms, depth_cap=self.depth_cap)
        self.board.push(eng_move)
        if self.board.is_game_over():
            r = self._terminal_reward()
            self.done = True
            return self._obs(), r, True, False, {}

        # Optional tiny shaping could be added here (we keep it 0 for purity)
        return self._obs(), 0.0, False, False, {}

    def render(self, mode="ansi"):
        return str(self.board)

    def close(self):
        self.engine.close()

    # ---- Helpers ----
    def _obs(self) -> Dict[str, np.ndarray]:
        return {
            "obs": board_to_obs(self.board),
            "action_mask": legal_action_mask(self.board),
        }

    def _terminal_reward(self) -> float:
        result = self.board.result()  # "1-0", "0-1", "1/2-1/2"
        if result == "1-0":
            return 1.0 if self.agent_color_white else -1.0
        if result == "0-1":
            return -1.0 if self.agent_color_white else 1.0
        return 0.0
