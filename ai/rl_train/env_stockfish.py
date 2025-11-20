import gymnasium as gym
import numpy as np
import chess
import requests
from gymnasium import spaces
from typing import Dict, Any, Tuple
import os

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
PROMOTION_DIRS = [(1, 0), (1, 1), (1, -1)]
PROMOTION_PIECES = ["q", "r", "b"]


def action_to_move(action: int, board: chess.Board) -> chess.Move | None:
    from_sq = action // 75
    move_type = action % 75

    if move_type < 56:
        dir_idx = move_type // 7
        steps = (move_type % 7) + 1
        dx, dy = QUEEN_DIRECTIONS[dir_idx]
        to_sq = from_sq + dx * steps * 8 + dy * steps
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type < 64:
        jump_idx = move_type - 56
        dx, dy = KNIGHT_JUMPS[jump_idx]
        to_sq = from_sq + dx * 8 + dy
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type < 73:
        promo_idx = move_type - 64
        dir_idx = promo_idx // 3
        piece_idx = promo_idx % 3
        dx, dy = PROMOTION_DIRS[dir_idx]
        to_sq = from_sq + dx * 8 + dy
        if 0 <= to_sq < 64:
            promo_piece = PROMOTION_PIECES[piece_idx]
            return chess.Move(
                from_sq,
                to_sq,
                promotion=chess.Piece.from_symbol(promo_piece).piece_type,
            )
    elif move_type == 73:
        to_sq = from_sq + (8 if board.turn == chess.WHITE else -8)
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type == 74:
        to_sq = from_sq + (16 if board.turn == chess.WHITE else -16)
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    return None


def move_to_action(move: chess.Move) -> int:
    from_sq, to_sq = move.from_square, move.to_square
    dx = (to_sq // 8) - (from_sq // 8)
    dy = (to_sq % 8) - (from_sq % 8)

    if move.promotion:
        promo_piece = chess.Piece(move.promotion).symbol().lower()
        if promo_piece not in PROMOTION_PIECES:
            return -1
        piece_idx = PROMOTION_PIECES.index(promo_piece)
        dir_map = {(1, 0): 0, (1, 1): 1, (1, -1): 2}
        if (dx, dy) not in dir_map:
            return -1
        dir_idx = dir_map[(dx, dy)]
        move_type = 64 + dir_idx * 3 + piece_idx
    elif abs(dx) <= 1 and abs(dy) <= 1 and (dx, dy) != (0, 0):
        if (dx, dy) not in QUEEN_DIRECTIONS:
            return -1
        dir_idx = QUEEN_DIRECTIONS.index((dx, dy))
        steps = max(abs(dx), abs(dy)) - 1
        if steps < 0 or steps > 6:
            return -1
        move_type = dir_idx * 7 + steps
    elif (dx, dy) in KNIGHT_JUMPS:
        move_type = 56 + KNIGHT_JUMPS.index((dx, dy))
    elif dx == 0 and abs(dy) == 1:
        move_type = 73
    elif dx == 0 and abs(dy) == 2:
        move_type = 74
    else:
        return -1
    return from_sq * 75 + move_type


class StockfishEnv(gym.Env):
    """Gym environment for training a chess agent against Stockfish via HTTP API."""

    metadata = {"render.modes": ["human"]}

    def __init__(self, config: Dict[str, Any] | None = None, **kwargs):
        super().__init__()
        cfg = dict(config or {})
        cfg.update(kwargs)  # allow both styles

        self.stockfish_api = cfg.get("stockfish_api", "http://127.0.0.1:8001")
        self.movetime_ms = int(cfg.get("movetime_ms", 150))

        # Chess board
        self.board = chess.Board()

        # Fixed action space: 4800 possible moves
        self.action_space = spaces.Discrete(4800)

        # Observation space: flattened 8x8x19 -> 1216 (12 piece planes + 7 extra)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(1216,), dtype=np.float32
        )

        # Reward shaping
        self.use_shaping = int(cfg.get("use_shaping", os.getenv("USE_SHAPING", 0)))
        self.shaping_clip_cp = int(
            cfg.get("shaping_clip_cp", os.getenv("SHAPING_CLIP_CP", 50))
        )

        # Color randomization
        self.randomize_player_color = cfg.get("randomize_player_color", False)

        # Tracking
        self.position_history = []
        self.illegal_moves = 0
        self.cp_deltas = []

        # Set max episode steps to prevent infinite horizon warnings
        self.spec = type("", (), {})()
        self.spec.max_episode_steps = 200
        self.spec.id = "StockfishEnv"

    def reset(self, *, seed=None, options=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self.board = chess.Board()
        # Randomize player color if enabled
        if self.randomize_player_color and np.random.random() < 0.5:
            self.board = self.board.mirror()
        # Ensure the board is in a valid legal state and not immediately terminal
        assert not self.board.is_game_over(), (
            "Reset should not produce an immediate terminal state"
        )
        self.position_history = [self.board.fen().split()[0]]
        self.illegal_moves = 0
        self.cp_deltas = []
        obs = self._board_to_obs()
        info = {"action_mask": self._get_action_mask()}
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        if action < 0 or action >= 4800:
            return (
                self._board_to_obs(),
                -1.0,
                True,
                False,
                {"invalid_action": True, "action_mask": self._get_action_mask()},
            )

        move = action_to_move(action, self.board)
        if (move is None) or (move not in self.board.legal_moves):
            self.illegal_moves += 1
            return (
                self._board_to_obs(),
                -1.0,
                True,
                False,
                {"invalid_action": True, "action_mask": self._get_action_mask()},
            )

        cp_before = self._get_evaluation() if self.use_shaping else 0.0

        self.board.push(move)
        self.position_history.append(self.board.fen().split()[0])

        terminated = self.board.is_game_over()
        reward = self._terminal_reward() if terminated else 0.0

        api_ms = 0
        if not terminated:
            sf_move, api_ms = self._get_stockfish_move()
            if sf_move:
                self.board.push(chess.Move.from_uci(sf_move))
                self.position_history.append(self.board.fen().split()[0])

            terminated = self.board.is_game_over()
            reward = self._terminal_reward() if terminated else 0.0

        if self.use_shaping and not terminated:
            cp_after = self._get_evaluation()
            delta_cp = cp_after - cp_before
            shaping = np.clip(
                delta_cp / 100.0,
                -self.shaping_clip_cp / 100.0,
                self.shaping_clip_cp / 100.0,
            )
            reward += float(shaping)
            self.cp_deltas.append(delta_cp)

        obs = self._board_to_obs()
        info = {"action_mask": self._get_action_mask(), "api_ms": api_ms}

        if terminated:
            if self.board.is_checkmate():
                outcome = "win" if self.board.turn == chess.BLACK else "loss"
                term = "checkmate"
            elif self.board.is_stalemate():
                outcome = "draw"
                term = "stalemate"
            elif self.board.is_repetition():
                outcome = "draw"
                term = "repetition"
            elif self.board.is_fifty_moves():
                outcome = "draw"
                term = "fifty_move"
            elif self.board.is_insufficient_material():
                outcome = "draw"
                term = "insufficient"
            else:
                # Fallback in rare/unknown cases
                term = "unknown"

            info["outcome"] = outcome
            info["termination"] = term
            info["ply_count"] = len(self.board.move_stack)
            info["played_as_white"] = (
                1
                if not self.randomize_player_color or self.board.turn == chess.WHITE
                else 0
            )
            info["stockfish_movetime_ms"] = self.movetime_ms
            info["illegal_moves"] = self.illegal_moves
            info["cp_deltas"] = self.cp_deltas

        return obs, reward, terminated, False, info

    def _get_stockfish_move(self) -> Tuple[str | None, int]:
        fen = self.board.fen()
        for attempt in range(2):
            try:
                r = requests.post(
                    f"{self.stockfish_api}/bestmove",
                    json={"fen": fen, "movetime": self.movetime_ms},
                    timeout=1.0,
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

        stm = 1.0 if self.board.turn == chess.WHITE else 0.0
        obs[:, :, 12] = stm
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
        obs[:, :, 17] = self.board.halfmove_clock / 100.0
        rep = self.position_history.count(self.board.fen().split()[0])
        obs[:, :, 18] = min(rep / 3.0, 1.0)
        return obs.reshape(-1)  # Flatten to (1216,)

    def _terminal_reward(self) -> float:
        if self.board.is_checkmate():
            return 1.0 if self.board.turn == chess.BLACK else -1.0
        if (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.is_fifty_moves()
            or self.board.is_repetition()
        ):
            return 0.0
        return 0.0

    def _get_action_mask(self) -> np.ndarray:
        mask = np.zeros(4800, dtype=bool)
        for m in self.board.legal_moves:
            a = move_to_action(m)
            if a != -1:
                mask[a] = True
        return mask

    def _get_evaluation(self) -> float:
        try:
            r = requests.post(
                f"{self.stockfish_api}/evaluate",
                json={"fen": self.board.fen()},
                timeout=1.0,
            )
            r.raise_for_status()
            data = r.json()
            cp = data.get("eval", {}).get("value", 0) if data.get("eval") else 0
            return cp / 100.0
        except Exception:
            return 0.0

    def render(self):
        print(self.board)
