# dataset/Data/ETL/pgn_sampler.py
from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Generator, Iterable, Optional, Tuple

import chess.pgn

# Local imports (package-relative)
try:
    # If run as module: python -m DeepChessIQ.dataset.Data.ETL.pgn_sampler
    from DeepChessIQ.dataset.Data.ETL.row_builder import build_game_rows
except Exception:
    # If imported relatively within the package
    from .row_builder import build_game_rows


# -------------------------
# Helpers
# -------------------------

def is_bot(name: Optional[str]) -> bool:
    """
    Heuristic to filter out obvious bots in usernames.
    Adjust to your dataset as needed.
    """
    if not name:
        return False
    s = name.strip().lower()
    return "bot" in s or s.endswith("_bot") or s.startswith("bot_")


def elo_bin_100_from_headers(headers: Dict[str, str]) -> Optional[int]:
    """Compute 100-Elo bin using avg(white, black) from raw headers."""
    def to_int(x):
        try:
            return int(x)
        except Exception:
            return None

    w = to_int(headers.get("WhiteElo"))
    b = to_int(headers.get("BlackElo"))
    if w is None and b is None:
        return None
    if w is None:
        avg = b
    elif b is None:
        avg = w
    else:
        avg = (w + b) // 2
    return (avg // 100) * 100 if avg is not None else None


def game_ply_count(game: chess.pgn.Game) -> int:
    """Fast ply counter from mainline (no branches)."""
    count = 0
    node = game
    while node.variations:
        node = node.variation(0)
        count += 1
    return count


# -------------------------
# Main generator
# -------------------------

def sample_games_by_elo_bin_streaming(
    pgn_path: str | Path,
    *,
    site: str = "lichess",
    skip_bots: bool = True,
) -> Generator[Tuple[dict, dict, Optional[int]], None, None]:
    """
    Sequentially stream games from a PGN and emit tuples:
        (core_row, text_row, elo_bin_100)

    - No randomization.
    - Guards against malformed games: skips if row_builder returns None.
    - Persists ply_count via build_game_rows(..., ply_count=...).
    """
    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN not found: {pgn_file}")

    with pgn_file.open("r", encoding="utf-8", errors="replace", newline="") as fp:
        while True:
            game = chess.pgn.read_game(fp)
            if game is None:
                return  # EOF

            headers = dict(game.headers)

            # Optional bot filter
            if skip_bots and (is_bot(headers.get("White")) or is_bot(headers.get("Black"))):
                continue

            # Build SAN string and compute ply_count from mainline moves
            board = game.board()
            sans: list[str] = []
            for mv in game.mainline_moves():
                sans.append(board.san(mv))
                board.push(mv)
            san_str = " ".join(sans)
            ply_count_val = len(sans)  # or game_ply_count(game)

            # Full PGN text (headers + moves, no comments/vars)
            exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
            movetext_full = game.accept(exporter)

            # Build rows (GUARD against None)
            rows = build_game_rows(headers, san_str, movetext_full, site=site, ply_count=ply_count_val)
            if not rows:
                # malformed or missing fields — skip safely
                continue

            core_row, text_row = rows
            bin100 = elo_bin_100_from_headers(headers)

            yield core_row, text_row, bin100


# -------------------------
# CLI (optional quick test)
# -------------------------

if __name__ == "__main__":
    import argparse, itertools

    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn", required=True)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    for i, (core, text, b) in enumerate(sample_games_by_elo_bin_streaming(args.pgn), start=1):
        print(f"[{i}] {core.get('white')} vs {core.get('black')}  bin={b}  ply={core.get('ply_count')}")
        if i >= args.limit:
            break
