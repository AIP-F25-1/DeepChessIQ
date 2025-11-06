import gymnasium as gym
import numpy as np
import chess
import requests
from gymnasium import spaces
from typing import Dict, Any, Tuple
import os


# AlphaZero-style 64×75 action space: 64 from_squares × 75 move_types = 4800
# Move types: 56 queen rays (8 dirs × 7 steps), 8 knight jumps, 9 promotions (3 dirs × 3 pieces), 2 pawn pushes (single/double)

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
PROMOTION_DIRS = [
    (1, 0),
    (1, 1),
    (1, -1),
]  # forward, right-forward, left-forward for White
PROMOTION_PIECES = ["q", "r", "b"]


def action_to_move(action: int, board: chess.Board) -> chess.Move:
    """Decode action index to chess.Move."""
    from_sq = action // 75
    move_type = action % 75

    if move_type < 56:  # Queen rays
        dir_idx = move_type // 7
        steps = (move_type % 7) + 1
        dx, dy = QUEEN_DIRECTIONS[dir_idx]
        to_sq = from_sq + dx * steps * 8 + dy * steps
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type < 64:  # Knight jumps
        jump_idx = move_type - 56
        dx, dy = KNIGHT_JUMPS[jump_idx]
        to_sq = from_sq + dx * 8 + dy
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type < 73:  # Promotions
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
    elif move_type == 73:  # Pawn single push
        if board.turn == chess.WHITE:
            to_sq = from_sq + 8
        else:
            to_sq = from_sq - 8
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)
    elif move_type == 74:  # Pawn double push
        if board.turn == chess.WHITE:
            to_sq = from_sq + 16
        else:
            to_sq = from_sq - 16
        if 0 <= to_sq < 64:
            return chess.Move(from_sq, to_sq)

    return None  # Invalid action


def move_to_action(move: chess.Move) -> int:
    """Encode chess.Move to action index."""
    from_sq = move.from_square
    to_sq = move.to_square
    dx = (to_sq // 8) - (from_sq // 8)
    dy = (to_sq % 8) - (from_sq % 8)

    if move.promotion:
        # Promotion
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
        # Queen ray
        if (dx, dy) not in QUEEN_DIRECTIONS:
            return -1
        dir_idx = QUEEN_DIRECTIONS.index((dx, dy))
        steps = max(abs(dx), abs(dy)) - 1
        if steps < 0 or steps > 6:
            return -1
        move_type = dir_idx * 7 + steps
    elif (dx, dy) in KNIGHT_JUMPS:
        # Knight jump
        jump_idx = KNIGHT_JUMPS.index((dx, dy))
        move_type = 56 + jump_idx
    elif dx == 0 and abs(dy) == 1:  # Pawn single push
        move_type = 73
    elif dx == 0 and abs(dy) == 2:  # Pawn double push
        move_type = 74
    else:
        return -1

    return from_sq * 75 + move_type


# Precompute mapping from UCI strings to action indices so legal moves can be masked quickly.
# This enumerates all encoded actions and converts them to UCI notation where valid.
UCI_TO_INDEX: Dict[str, int] = {}
for action_idx in range(4800):
    move = action_to_move(action_idx, chess.Board())
    if move is not None:
        try:
            uci = move.uci()
            UCI_TO_INDEX[uci] = action_idx
        except Exception:
            # Skip any move that cannot be converted to UCI
            continue


class StockfishEnv(gym.Env):
    """
    Gym environment for RL agent to play chess against Stockfish via FastAPI.
    Agent plays as white, Stockfish as black.
    """

    def __init__(
        self, stockfish_api: str = "http://127.0.0.1:8001", movetime_ms: int = 150
    ):
        super().__init__()
        self.stockfish_api = stockfish_api
        self.movetime_ms = movetime_ms

        # Chess board
        self.board = chess.Board()

        # Fixed action space: 4800 possible moves
        self.action_space = spaces.Discrete(4800)

        # Observation space: 8x8x19 (12 piece planes + 7 extra)
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(8, 8, 19), dtype=np.float32
        )

        # Reward shaping
        self.use_shaping = int(os.getenv("USE_SHAPING", 0))
        self.shaping_clip_cp = int(os.getenv("SHAPING_CLIP_CP", 50))

        # Track repetitions for normalization
        self.position_history = []

        # Track for callbacks
        self.illegal_moves = 0
        self.cp_deltas = []

    def reset(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        self.board = chess.Board()
        self.position_history = [self.board.fen().split()[0]]  # Track for repetitions
        self.illegal_moves = 0
        self.cp_deltas = []
        obs = self._board_to_obs()
        info = {"action_mask": self._get_action_mask()}
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # Decode action to move
        if action < 0 or action >= 4800:
            return (
                self._board_to_obs(),
                -1.0,
                True,
                False,
                {"invalid_action": True, "action_mask": self._get_action_mask()},
            )

        move = action_to_move(action, self.board)
        if move is None or move not in self.board.legal_moves:
            self.illegal_moves += 1
            return (
                self._board_to_obs(),
                -1.0,
                True,
                False,
                {"invalid_action": True, "action_mask": self._get_action_mask()},
            )

        # Shaping: eval before move
        cp_before = 0.0
        if self.use_shaping:
            cp_before = self._get_evaluation()

        # Push agent's move
        self.board.push(move)
        self.position_history.append(self.board.fen().split()[0])

        # Check terminal after agent's move
        done = self.board.is_game_over()
        reward = self._get_reward() if done else 0.0

        if not done:
            # Stockfish's turn
            sf_move, api_ms = self._get_stockfish_move()
            if sf_move:
                self.board.push(chess.Move.from_uci(sf_move))
                self.position_history.append(self.board.fen().split()[0])

            # Check terminal after Stockfish's move
            done = self.board.is_game_over()
            reward = self._get_reward() if done else 0.0

        # Shaping: add delta if enabled and not terminal
        if self.use_shaping and not done:
            cp_after = self._get_evaluation()
            delta_cp = cp_after - cp_before
            shaping_reward = np.clip(
                delta_cp / 100.0,
                -self.shaping_clip_cp / 100.0,
                self.shaping_clip_cp / 100.0,
            )
            reward += shaping_reward
            self.cp_deltas.append(delta_cp)

        obs = self._board_to_obs()
        info = {
            "action_mask": self._get_action_mask(),
            "api_ms": api_ms if "api_ms" in locals() else 0,
        }

        # Add outcome and tracking for callbacks
        if done:
            if self.board.is_checkmate():
                if self.board.turn == chess.WHITE:
                    info["outcome"] = "loss"  # Agent lost
                else:
                    info["outcome"] = "win"  # Agent won
            else:
                info["outcome"] = "draw"  # Any draw
            info["illegal_moves"] = self.illegal_moves
            info["cp_deltas"] = self.cp_deltas

        return obs, reward, done, False, info  # truncated=False

    def _get_stockfish_move(self) -> Tuple[str, int]:
        fen = self.board.fen()
        for attempt in range(2):  # One quick retry on timeout
            try:
                response = requests.post(
                    f"{self.stockfish_api}/bestmove",
                    json={"fen": fen, "movetime": self.movetime_ms},
                    timeout=1.0,
                )
                response.raise_for_status()
                data = response.json()
                return data["uci"], data.get("used", {}).get("elapsed_ms", 0)
            except requests.exceptions.Timeout:
                if attempt == 0:
                    print("Stockfish API timeout, retrying...")
                    continue
                else:
                    print("Stockfish API timeout after retry")
                    return None, 0
            except Exception as e:
                print(f"Stockfish API error: {e}")
                return None, 0
        return None, 0

    def _board_to_obs(self) -> np.ndarray:
        # Convert board to 8x8x19 tensor
        obs = np.zeros((8, 8, 19), dtype=np.float32)
        piece_map = {
            chess.PAWN: 0,
            chess.KNIGHT: 1,
            chess.BISHOP: 2,
            chess.ROOK: 3,
            chess.QUEEN: 4,
            chess.KING: 5,
        }
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row, col = divmod(square, 8)
                channel = piece_map[piece.piece_type] + (
                    6 if piece.color == chess.BLACK else 0
                )
                obs[row, col, channel] = 1.0

        # Extra planes: stm, castling rights, halfmove_norm, repetition_norm
        stm = 1.0 if self.board.turn == chess.WHITE else 0.0
        obs[:, :, 12] = stm  # Side to move

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

        # Halfmove clock normalized (0-1)
        halfmove_norm = self.board.halfmove_clock / 100.0
        obs[:, :, 17] = halfmove_norm

        # Repetition count normalized (0-1)
        repetition_count = self.position_history.count(self.board.fen().split()[0])
        repetition_norm = min(repetition_count / 3.0, 1.0)
        obs[:, :, 18] = repetition_norm

        return obs

    def _get_reward(self) -> float:
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:
                return -1.0  # Agent lost
            else:
                return 1.0  # Agent won
        elif (
            self.board.is_stalemate()
            or self.board.is_insufficient_material()
            or self.board.is_fifty_moves()
            or self.board.is_repetition()
        ):
            return 0.0  # Draw
        else:
            return 0.0  # Game not over

    def _get_action_mask(self) -> np.ndarray:
        mask = np.zeros(4800, dtype=bool)
        for move in self.board.legal_moves:
            action = move_to_action(move)
            if action != -1:
                mask[action] = True
        return mask

    def _get_evaluation(self) -> float:
        fen = self.board.fen()
        try:
            response = requests.post(
                f"{self.stockfish_api}/evaluate",
                json={"fen": fen},
                timeout=1.0,
            )
            response.raise_for_status()
            data = response.json()
            eval_cp = data.get("eval", {}).get("value", 0) if data.get("eval") else 0
            return eval_cp / 100.0  # Convert to pawns
        except Exception as e:
            print(f"Evaluation API error: {e}")
            return 0.0

    def render(self, mode="human"):
        print(self.board)

    def close(self):
        pass
