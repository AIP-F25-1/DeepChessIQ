import random
import chess.pgn
from pathlib import Path
from typing import Iterator, Literal

from .row_builder import build_game_rows

def get_elo_bin(white_elo: int, black_elo: int) -> int | None:
    try:
        avg = (int(white_elo) + int(black_elo)) // 2
        return (avg // 100) * 100
    except:
        return None

def stream_games_from_pgn(pgn_path: Path) -> Iterator[tuple[dict, str, str]]:
    with pgn_path.open("r", encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            headers = dict(game.headers)
            san = game.board().variation_san(game.mainline_moves())
            fulltext = str(game).split("\n\n", maxsplit=1)[-1].strip()
            yield headers, san, fulltext

def sample_games_by_elo_bin(
    pgn_path: Path,
    elo_bins: list[int],
    games_per_bin: int,
    site: Literal["lichess", "chesscom"] = "lichess",
    seed: int = 42
) -> list[tuple[dict, dict]]:
    """
    Returns: List of (core_row, text_row)
    """
    random.seed(seed)
    buffer = {b: [] for b in elo_bins}
    result = []

    total_seen = 0
    with pgn_path.open("r", encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                print("📁 Reached end of PGN file.")
                break

            total_seen += 1
            if total_seen % 10_000 == 0:
                print(f"👀 Scanned {total_seen:,} games so far...")

            headers = dict(game.headers)
            try:
                white_elo = int(headers.get("WhiteElo", 0))
                black_elo = int(headers.get("BlackElo", 0))
            except ValueError:
                continue

            bin_ = get_elo_bin(white_elo, black_elo)
            if bin_ not in buffer:
                continue

            if len(buffer[bin_]) >= games_per_bin * 3:
                continue

            san = game.board().variation_san(game.mainline_moves())
            fulltext = str(game).split("\n\n", maxsplit=1)[-1].strip()
            core, text = build_game_rows(headers, san, fulltext, site=site)
            buffer[bin_].append((core, text))

            # ✅ EARLY STOP if all bins are filled
            if all(len(glist) >= games_per_bin * 3 for glist in buffer.values()):
                print("✅ Collected enough buffer for all bins. Stopping early.")
                break

    # 🎯 Final sample per bin
    for bin_, games in buffer.items():
        sampled = random.sample(games, min(games_per_bin, len(games)))
        result.extend(sampled)

    print(f"🎯 Total selected: {len(result)}")
    return result
