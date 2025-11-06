# data_utils.py
from __future__ import annotations
import json
from typing import Dict, List, Optional, Tuple
import numpy as np
import chess

# ----- Action encoding (must match your RL env) -----
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

# ----- Observation features (simple and fast) -----
OBS_SIZE = 12*64 + 6 + 2  # 12 piece planes + 6 material + side + castling + ep -> packed

def board_to_obs(board: chess.Board) -> np.ndarray:
    planes = np.zeros((12, 64), dtype=np.float32)
    piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
    for color in [chess.WHITE, chess.BLACK]:
        base = 0 if color == chess.WHITE else 6
        for i, pt in enumerate(piece_types):
            for sq in board.pieces(pt, color):
                planes[base + i, sq] = 1.0
    planes = planes.reshape(-1)

    side = np.array([1.0 if board.turn == chess.WHITE else 0.0], dtype=np.float32)
    castling = np.array([
        1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0,
        1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0,
        1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0,
        1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0,
    ], dtype=np.float32)
    ep = np.array([1.0 if board.ep_square is not None else 0.0], dtype=np.float32)

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

# ----- Targets from human histogram & engine list -----
def histogram_to_target(board: chess.Board, human_hist: List[Tuple[str, int]], alpha_smooth: float = 0.5) -> np.ndarray:
    """
    Convert [(uci, count), ...] to a probability vector over ACTION_SPACE_SIZE with Dirichlet smoothing.
    Only legal moves receive mass; renormalizes.
    """
    mask = legal_action_mask(board)
    y = np.zeros((ACTION_SPACE_SIZE,), dtype=np.float32)
    total = 0.0
    for uci, cnt in human_hist:
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            continue
        if mv not in board.legal_moves:
            continue
        idx = move_to_index(mv)
        y[idx] += float(cnt)
        total += float(cnt)
    # Dirichlet smoothing on legal moves only
    y = y + alpha_smooth * mask
    s = y.sum()
    if s <= 0:
        # fallback: uniform over legal moves
        n_legal = mask.sum()
        if n_legal > 0:
            y = mask / n_legal
    else:
        y /= s
    return y

def engine_softmax_target(board: chess.Board, engine_topN: List[Tuple[str, float]], temperature_cp: float = 200.0) -> np.ndarray:
    """
    Build a soft target over legal actions from engine evals (centipawns), only for provided candidates.
    engine_topN = [(uci, eval_cp), ...]   (eval_cp can be None; such entries are skipped)
    """
    mask = legal_action_mask(board)
    logits = np.full((ACTION_SPACE_SIZE,), -1e9, dtype=np.float32)
    any_valid = False
    for uci, cp in engine_topN:
        if cp is None:
            continue
        try:
            mv = chess.Move.from_uci(uci)
        except Exception:
            continue
        if mv not in board.legal_moves:
            continue
        idx = move_to_index(mv)
        logits[idx] = float(cp) / max(1.0, temperature_cp)
        any_valid = True
    if not any_valid:
        # fallback uniform over legal
        n = mask.sum()
        return (mask / n) if n > 0 else np.zeros_like(mask)
    # softmax over all actions (only candidates have finite logits)
    m = np.max(logits)
    exps = np.exp(logits - m)
    p = exps / np.sum(exps)
    return p
