#!/usr/bin/env python3
"""
Quick PGN → Engine Evaluation Test
---------------------------------
Reads one PGN file, sends each move's FEN to your running Stockfish API,
and logs move, eval, and time.

Make sure your engine service is already running at http://127.0.0.1:8001
"""

import requests
import chess.pgn
from pathlib import Path
from time import sleep

# === CONFIG ===
ENGINE_URL = "http://127.0.0.1:8001/bestmove"
PGN_FILE = Path("ai\data\sample_game.pgn")  # change path if needed
SLEEP_BETWEEN = 0.1  # seconds between API calls (to avoid hammering)


# === MAIN ===
def evaluate_game(pgn_path: Path):
    if not pgn_path.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_path}")

    with open(pgn_path, encoding="utf-8") as f:
        game = chess.pgn.read_game(f)

    board = game.board()
    print(
        f"Loaded game: {game.headers.get('Event', 'Unknown')} — {game.headers.get('White')} vs {game.headers.get('Black')}"
    )
    print("=" * 70)

    for idx, move in enumerate(game.mainline_moves(), 1):
        # pretty move text BEFORE pushing
        san = board.san(move)
        move_no = (idx + 1) // 2
        prefix = f"{move_no}. " if (idx % 2 == 1) else f"{move_no}... "

        # apply the PGN move
        board.push(move)
        fen = board.fen()

        # call engine (your request code here)
        r = requests.post(ENGINE_URL, json={"fen": fen}, timeout=10)
        data = r.json()
        used = data.get("used", {})
        eval_info = data.get("eval", {})

        print(
            f"[{idx:02d}] {prefix}{san:<6} | eval: {eval_info.get('value')} {eval_info.get('type')} "
            f"| engine_reply: {data.get('uci')} | time: {used.get('elapsed_ms')} ms | depth≈{used.get('approx_depth')}"
        )


if __name__ == "__main__":
    evaluate_game(PGN_FILE)
