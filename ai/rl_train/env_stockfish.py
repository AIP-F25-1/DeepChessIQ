# ai/rl_train/env_stockfish.py
import os
from typing import Dict, Any, Tuple

import chess
import gymnasium as gym
import numpy as np
import requests
from gymnasium import spaces

QUEEN_DIRECTIONS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
]
KNIGHT_JUMPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

PROMOTION_DIRS_WHITE = [(1, 0), (1, 1), (1, -1)]
PROMOTION_DIRS_BLACK = [(-1, 0), (-1, -1), (-1, 1)]
PROMOTION_PIECES = ["q", "r", "b"]  # can add 'n' later

NUM_ACTIONS = 64 * 75  # 4800


# ---------- ACTION ENCODER / DECODER ----------


def action_to_move(action: int, board: chess.Board) -> chess.Move | None:
    """Decode integer action -> chess.Move using the same scheme as move_to_action."""
    from_sq = action // 75
    move_type = action % 75

    # Sliding moves: 0–55  (8 directions * 7 step lengths)
    if move_type < 56:
        dir_idx = move_type // 7
        steps = (move_type % 7) + 1  # steps in squares (1..7)
        dx, dy = QUEEN_DIRECTIONS[dir_idx]
        to_sq = from_sq + dx * steps * 8 + dy * steps
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)

    # Knight jumps: 56–63
    elif move_type < 64:
        jump_idx = move_type - 56
        dx, dy = KNIGHT_JUMPS[jump_idx]
        to_sq = from_sq + dx * 8 + dy
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)

    # Promotions: 64–72 (3 dirs × 3 pieces)
    elif move_type < 73:
        promo_idx = move_type - 64
        dir_idx = promo_idx // 3
        piece_idx = promo_idx % 3
        dirs = (
            PROMOTION_DIRS_WHITE if board.turn == chess.WHITE else PROMOTION_DIRS_BLACK
        )
        dx, dy = dirs[dir_idx]
        to_sq = from_sq + dx * 8 + dy
        if 0 <= to_sq < 64:
            promo_piece = PROMOTION_PIECES[piece_idx]
            return chess.Move(
                from_sq,
                to_sq,
                promotion=chess.Piece.from_symbol(promo_piece).piece_type,
            )

    # Single pawn push (relative to side to move): 73
    elif move_type == 73:
        to_sq = from_sq + (8 if board.turn == chess.WHITE else -8)
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)

    # Double pawn push: 74
    elif move_type == 74:
        to_sq = from_sq + (16 if board.turn == chess.WHITE else -16)
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)

    return None


def move_to_action(board: chess.Board, move: chess.Move) -> int:
    """Encode chess.Move -> integer action.

    This is the inverse of action_to_move. Any legal move that cannot be
    encoded returns -1 and will be excluded from the mask.
    """
    from_sq, to_sq = move.from_square, move.to_square
    dx = (to_sq // 8) - (from_sq // 8)  # rank delta
    dy = (to_sq % 8) - (from_sq % 8)  # file delta

    # Promotions
    if move.promotion:
        promo_piece = chess.Piece(move.promotion).symbol().lower()
        if promo_piece not in PROMOTION_PIECES:
            return -1
        piece_idx = PROMOTION_PIECES.index(promo_piece)
        dir_map_white = {(1, 0): 0, (1, 1): 1, (1, -1): 2}
        dir_map_black = {(-1, 0): 0, (-1, -1): 1, (-1, 1): 2}
        dir_map = dir_map_white if board.turn == chess.WHITE else dir_map_black
        key = (dx, dy)
        if key not in dir_map:
            return -1
        dir_idx = dir_map[key]
        move_type = 64 + dir_idx * 3 + piece_idx

    # Sliding moves (queen, rook, bishop style)
    elif (dx, dy) != (0, 0) and (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
        # Normalise to unit direction
        sx = 0 if dx == 0 else dx // abs(dx)
        sy = 0 if dy == 0 else dy // abs(dy)
        if (sx, sy) not in QUEEN_DIRECTIONS:
            return -1
        dir_idx = QUEEN_DIRECTIONS.index((sx, sy))

        distance = max(abs(dx), abs(dy))
        steps = distance - 1  # stored as 0..6
        if steps < 0 or steps > 6:
            return -1
        move_type = dir_idx * 7 + steps

    # Knight jumps
    elif (dx, dy) in KNIGHT_JUMPS:
        move_type = 56 + KNIGHT_JUMPS.index((dx, dy))

    # Pawn pushes (no promotion)
    elif dy == 0 and abs(dx) == 1:
        move_type = 73  # single push
    elif dy == 0 and abs(dx) == 2:
        move_type = 74  # double push
    else:
        return -1

    return from_sq * 75 + move_type


# ---------- ENVIRONMENT ----------


class StockfishEnv(gym.Env):
    """Gymnasium env: train a chess agent vs Stockfish HTTP API."""

    metadata = {"render_modes": ["human"]}

    def __init__(self, config: Dict[str, Any] | None = None, **kwargs):
        super().__init__()
        cfg = dict(config or {})
        cfg.update(kwargs)

        self.stockfish_api = cfg.get("stockfish_api", "http://127.0.0.1:8001")
        self.movetime_ms = int(cfg.get("movetime_ms", 150))

        # Reward shaping
        self.use_shaping = int(cfg.get("use_shaping", os.getenv("USE_SHAPING", 0)))
        self.shaping_clip_cp = int(
            cfg.get("shaping_clip_cp", os.getenv("SHAPING_CLIP_CP", 50))
        )

        # Color randomization
        self.randomize_player_color = cfg.get("randomize_player_color", False)

        # Debug flag
        self.debug = bool(int(cfg.get("debug", os.getenv("ENV_DEBUG", "0"))))

        # Chess board
        self.board = chess.Board()

        # Action & observation spaces
        self.action_space = spaces.Discrete(NUM_ACTIONS)

        board_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(8, 8, 19),
            dtype=np.float32,
        )
        mask_space = spaces.Box(
            low=0,
            high=1,
            shape=(NUM_ACTIONS,),  # <-- must match action_space.n
            dtype=np.int8,
        )

        # Dict obs: {"obs": board_planes, "action_mask": mask}
        self.observation_space = spaces.Dict(
            {
                "obs": board_space,
                "action_mask": mask_space,
            }
        )

        # Tracking
        self.position_history: list[str] = []
        self.illegal_moves = 0
        self.cp_deltas: list[float] = []
        self.played_as_white = 1
        self.last_obs: Dict[str, Any] | None = None

        # Prevent infinite horizon warnings
        self.spec = type("", (), {})()
        self.spec.max_episode_steps = 200
        self.spec.id = "StockfishEnv"

    # ----- Core API -----

    def reset(
        self, *, seed=None, options=None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        super().reset(seed=seed)
        self.board = chess.Board()
        if self.randomize_player_color and np.random.random() < 0.5:
            self.board = self.board.mirror()

        assert not self.board.is_game_over(), "Reset produced terminal state."

        self.position_history = [self.board.fen().split()[0]]
        self.illegal_moves = 0
        self.cp_deltas = []
        self.played_as_white = 1 if self.board.turn == chess.WHITE else 0

        board_obs = self._board_to_obs()
        mask = self._get_action_mask()

        obs = {"obs": board_obs, "action_mask": mask}
        info = {"action_mask": mask}
        self.last_obs = obs
        return obs, info

    def step(
        self, action: int
    ) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        # Cast to plain int
        if not isinstance(action, (int, np.integer)):
            action = int(action)

        mask = self._get_action_mask()

        # Out-of-range
        if action < 0 or action >= NUM_ACTIONS:
            board_obs = self._board_to_obs()
            obs = {"obs": board_obs, "action_mask": mask}
            self.last_obs = obs
            return (
                obs,
                -0.1,
                False,
                False,
                {
                    "invalid_action": True,
                    "action_mask": mask,
                    "reason": "out_of_range",
                },
            )

        move = action_to_move(action, self.board)
        is_legal = (move is not None) and (move in self.board.legal_moves)

        # Illegal: soft penalty, don't terminate
        if not is_legal:
            self.illegal_moves += 1
            board_obs = self._board_to_obs()
            obs = {"obs": board_obs, "action_mask": mask}
            self.last_obs = obs
            return (
                obs,
                -0.1,
                False,
                False,
                {
                    "invalid_action": True,
                    "action_mask": mask,
                    "reason": "illegal_move",
                },
            )

        # ----- Legal move flow -----
        cp_before = self._get_evaluation() if self.use_shaping else 0.0
        outcome_str: str | None = None
        term_str: str | None = None

        self.board.push(move)
        self.position_history.append(self.board.fen().split()[0])

        # Check if game ended after agent move
        terminated = self.board.is_game_over()
        reward = 0.0
        api_ms = 0

        if terminated:
            reward = self._terminal_reward()
        else:
            # Stockfish responds
            sf_uci, api_ms = self._get_stockfish_move()
            if sf_uci:
                sf_move = chess.Move.from_uci(sf_uci)
                self.board.push(sf_move)
                self.position_history.append(self.board.fen().split()[0])
                terminated = self.board.is_game_over()
                if terminated:
                    reward = self._terminal_reward()
                elif self.use_shaping:
                    # Reward shaping in "pawns"
                    cp_after = self._get_evaluation()
                    delta = cp_after - cp_before
                    clipped = np.clip(
                        delta,
                        -self.shaping_clip_cp / 100.0,
                        self.shaping_clip_cp / 100.0,
                    )
                    reward = float(clipped)
                    self.cp_deltas.append(float(delta))
            else:
                # Stockfish API failed -> terminate episode
                terminated = True
                reward = 0.0
                outcome_str = "unknown"
                term_str = "STOCKFISH_ERROR"

        board_obs = self._board_to_obs()
        new_mask = self._get_action_mask()

        obs = {"obs": board_obs, "action_mask": new_mask}
        self.last_obs = obs

        info: Dict[str, Any] = {"action_mask": new_mask, "api_ms": api_ms}

        if terminated:
            # If not already set (e.g., STOCKFISH_ERROR), infer outcome/term from board
            if outcome_str is None or term_str is None:
                if self.board.is_checkmate():
                    loser_is_white = self.board.turn == chess.WHITE
                    winner_is_white = not loser_is_white
                    outcome_str = (
                        "win"
                        if winner_is_white == (self.played_as_white == 1)
                        else "loss"
                    )
                    term_str = "checkmate"
                elif self.board.is_stalemate():
                    outcome_str, term_str = "draw", "stalemate"
                elif self.board.is_repetition():
                    outcome_str, term_str = "draw", "repetition"
                elif self.board.is_fifty_moves():
                    outcome_str, term_str = "draw", "fifty_move"
                elif self.board.is_insufficient_material():
                    outcome_str, term_str = "draw", "insufficient"
                else:
                    outcome_str, term_str = "unknown", "UNKNOWN"

            info.update(
                {
                    "outcome": outcome_str,
                    "termination": term_str,
                    "ply_count": len(self.board.move_stack),
                    "played_as_white": self.played_as_white,
                    "stockfish_movetime_ms": self.movetime_ms,
                    "illegal_moves": self.illegal_moves,
                    "cp_deltas": self.cp_deltas,
                }
            )

        return obs, float(reward), terminated, False, info

    # ----- Helpers -----

    def _get_stockfish_move(self) -> Tuple[str | None, int]:
        fen = self.board.fen()
        for attempt in range(2):
            try:
                r = requests.post(
                    f"{self.stockfish_api}/bestmove",
                    json={"fen": fen, "movetime": self.movetime_ms},
                    timeout=2.0,
                )
                r.raise_for_status()
                data = r.json()
                return data["uci"], data.get("used", {}).get("elapsed_ms", 0)
            except requests.exceptions.Timeout:
                if attempt == 0:
                    continue
                return None, 0
            except Exception:
                return None, 0
        return None, 0

    def _board_to_obs(self) -> np.ndarray:
        obs = np.zeros((8, 8, 19), dtype=np.float32)
        piece_map = {
            chess.PAWN: 0,
            chess.KNIGHT: 1,
            chess.BISHOP: 2,
            chess.ROOK: 3,
            chess.QUEEN: 4,
            chess.KING: 5,
        }
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if p:
                r, c = divmod(sq, 8)
                ch = piece_map[p.piece_type] + (6 if p.color == chess.BLACK else 0)
                obs[r, c, ch] = 1.0

        # Side to move
        stm = 1.0 if self.board.turn == chess.WHITE else 0.0
        obs[:, :, 12] = stm

        # Castling rights
        obs[:, :, 13] = (
            1.0 if self.board.has_kingside_castling_rights(chess.WHITE) else 0.0
        )
        obs[:, :, 14] = (
            1.0 if self.board.has_queenside_castling_rights(chess.WHITE) else 0.0
        )
        obs[:, :, 15] = (
            1.0 if self.board.has_kingside_castling_rights(chess.BLACK) else 0.0
        )
        obs[:, :, 16] = (
            1.0 if self.board.has_queenside_castling_rights(chess.BLACK) else 0.0
        )

        # Halfmove clock (normalised)
        obs[:, :, 17] = self.board.halfmove_clock / 100.0

        # Repetition count (0..1, capped at 3)
        rep = self.position_history.count(self.board.fen().split()[0])
        obs[:, :, 18] = min(rep / 3.0, 1.0)

        return obs

    def _terminal_reward(self) -> float:
        if self.board.is_checkmate():
            loser_is_white = self.board.turn == chess.WHITE
            winner_is_white = not loser_is_white
            return 1.0 if winner_is_white == (self.played_as_white == 1) else -1.0
        if (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.is_fifty_moves()
            or self.board.is_repetition()
        ):
            return 0.0
        return 0.0

    def _get_action_mask(self) -> np.ndarray:
        mask = np.zeros(NUM_ACTIONS, dtype=np.int8)
        for m in self.board.legal_moves:
            a = move_to_action(self.board, m)
            if a != -1:
                mask[a] = 1
        return mask

    def _get_evaluation(self) -> float:
        try:
            r = requests.post(
                f"{self.stockfish_api}/evaluate",
                json={"fen": self.board.fen()},
                timeout=2.0,
            )
            r.raise_for_status()
            data = r.json()
            cp = data.get("eval", {}).get("value", 0) if data.get("eval") else 0
            # Return in "pawns"
            return cp / 100.0
        except Exception:
            return 0.0

    def render(self):
        print(self.board)
