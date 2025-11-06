# imitation_dataset.py
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import json
import random
import numpy as np
import torch
from torch.utils.data import Dataset

import chess

from data_utils import board_to_obs, legal_action_mask, move_to_index, histogram_to_target, engine_softmax_target, ACTION_SPACE_SIZE

class ImitationRow:
    __slots__ = ("fen", "label_uci", "human_hist", "engine_top")
    def __init__(self, fen: str, label_uci: Optional[str],
                 human_hist: List[Tuple[str, int]],
                 engine_top: List[Tuple[str, Optional[float]]]):
        self.fen = fen
        self.label_uci = label_uci
        self.human_hist = human_hist
        self.engine_top = engine_top

class ImitationDataset(Dataset):
    def __init__(self, rows: List[ImitationRow], use_label_top1: bool = False):
        self.rows = rows
        self.use_label_top1 = use_label_top1

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx: int):
        r = self.rows[idx]
        board = chess.Board(r.fen)

        obs = board_to_obs(board)
        mask = legal_action_mask(board)

        # Targets
        y_human = histogram_to_target(board, r.human_hist, alpha_smooth=0.5)

        # Optional top-1 label (supervised CE) from label_uci if available
        label_idx = -1
        if self.use_label_top1 and r.label_uci:
            try:
                mv = chess.Move.from_uci(r.label_uci)
                if mv in board.legal_moves:
                    label_idx = move_to_index(mv)
            except Exception:
                pass

        # Engine soft target
        y_engine = engine_softmax_target(board, r.engine_top, temperature_cp=200.0)

        return {
            "obs": torch.from_numpy(obs).float(),
            "mask": torch.from_numpy(mask).float(),
            "y_human": torch.from_numpy(y_human).float(),
            "y_engine": torch.from_numpy(y_engine).float(),
            "label_idx": torch.tensor(label_idx, dtype=torch.long),
        }

# ---- Simple file loaders (replace with your Parquet reader if you have one) ----
def load_rows_from_csv(path: str, limit: Optional[int] = None) -> List[ImitationRow]:
    import csv
    rows: List[ImitationRow] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            fen = row["fen"].strip()
            label_uci = row.get("label_uci", "").strip() or None
            human_hist = json.loads(row.get("human_hist_json", "[]"))
            engine_top = json.loads(row.get("engine_top20_json", "[]"))
            rows.append(ImitationRow(fen, label_uci, human_hist, engine_top))
            if limit and len(rows) >= limit:
                break
    return rows

def train_val_split(rows: List[ImitationRow], val_frac: float = 0.05, seed: int = 42):
    rng = random.Random(seed)
    idxs = list(range(len(rows)))
    rng.shuffle(idxs)
    cut = int(len(rows) * (1 - val_frac))
    train_idx, val_idx = idxs[:cut], idxs[cut:]
    train_rows = [rows[i] for i in train_idx]
    val_rows = [rows[i] for i in val_idx]
    return train_rows, val_rows
