import random
import re
from collections import Counter
from pathlib import Path
from typing import Iterator, Literal, Optional

import chess.pgn

from .row_builder import build_game_rows


def get_elo_bin(white_elo: int, black_elo: int) -> Optional[int]:
    try:
        avg = (int(white_elo) + int(black_elo)) // 2
        return (avg // 100) * 100
    except Exception:
        return None


def is_bot(name: Optional[str]) -> bool:
    if not name:
        return False
    return name.endswith("BOT") or name.endswith("_bot") or "bot" in name.lower()


def parse_year(utc_date: str) -> Optional[int]:
    if not utc_date or "????" in utc_date:
        return None
    m = re.match(r"(\d{4})\.", utc_date)
    return int(m.group(1)) if m else None


def estimate_time_category(timecontrol: Optional[str]) -> Optional[str]:
    if not timecontrol or timecontrol == "-":
        return None
    base, inc = 0, 0
    if "+" in timecontrol:
        p = timecontrol.split("+", 1)
        try:
            base = int(p[0])
            inc = int(p[1])
        except Exception:
            return None
    else:
        try:
            base = int(timecontrol)
        except Exception:
            return None
    total = base + 40 * inc
    if total <= 120:
        return "bullet"
    if total <= 480:
        return "blitz"
    if total <= 1500:
        return "rapid"
    return "classical"


def game_ply_count(game: chess.pgn.Game) -> int:
    try:
        return game.end().ply()
    except Exception:
        return 0


def sample_games_by_elo_bin_streaming(
    pgn_path: Path,
    elo_bins: list[int],
    games_per_bin: int,
    site: Literal["lichess", "chesscom"] = "lichess",
    seed: int = 42,
    *,
    allowed_timecats: Optional[set[str]] = None,
    allowed_variants: Optional[set[str]] = None,
    rated_only: bool = True,
    min_year: Optional[int] = None,
    min_plies: int = 6,
    exclude_bots: bool = True,
    max_games_per_player_per_bin: int = 3,
    chunk_size_per_bin: int = 400,
) -> Iterator[tuple[dict, dict, int]]:
    """
    Stream PGN file sequentially, keep small per-bin buffers,
    and yield selected games incrementally.

    Yields: (core_row, text_row, elo_bin)
    """

    rng = random.Random(seed)

    emitted_per_bin: dict[int, int] = {b: 0 for b in elo_bins}
    buffers: dict[int, list[tuple[dict, dict, str, str]]] = {b: [] for b in elo_bins}
    per_player_cap: dict[int, Counter[str]] = {b: Counter() for b in elo_bins}

    def bin_full(b: int) -> bool:
        return emitted_per_bin[b] >= games_per_bin

    def need_any() -> bool:
        return any(emitted_per_bin[b] < games_per_bin for b in elo_bins)

    def can_add_player(b: int, white: Optional[str], black: Optional[str]) -> bool:
        for p in (white, black):
            if not p:
                continue
            if per_player_cap[b][p] >= max_games_per_player_per_bin:
                return False
        return True

    def record_players(b: int, white: Optional[str], black: Optional[str], delta: int):
        for p in (white, black):
            if not p:
                continue
            per_player_cap[b][p] += delta
            if per_player_cap[b][p] <= 0:
                del per_player_cap[b][p]

    def flush_bin(b: int):
        remaining = max(0, games_per_bin - emitted_per_bin[b])
        if remaining == 0 or not buffers[b]:
            buffers[b].clear()
            return

        take = min(remaining, len(buffers[b]))
        if take < len(buffers[b]):
            chosen_idx = set(rng.sample(range(len(buffers[b])), take))
        else:
            chosen_idx = set(range(len(buffers[b])))

        new_buf = []
        for i, (core_row, text_row, w, k) in enumerate(buffers[b]):
            if i in chosen_idx:
                record_players(b, w, k, +1)
                emitted_per_bin[b] += 1
                yield (core_row, text_row, b)
            else:
                new_buf.append((core_row, text_row, w, k))

        buffers[b] = new_buf

    with pgn_path.open("r", encoding="utf-8") as f:
        scanned = 0
        while need_any():
            game = chess.pgn.read_game(f)
            if game is None:
                break

            scanned += 1
            if scanned % 10000 == 0:
                print(f"Scanned {scanned:,} games...")

            headers = dict(game.headers)
            white = headers.get("White")
            black = headers.get("Black")

            res = headers.get("Result")
            if res not in ("1-0", "0-1", "1/2-1/2"):
                continue
            if exclude_bots and (is_bot(white) or is_bot(black)):
                continue

            variant = headers.get("Variant", "Standard")
            if allowed_variants and variant not in allowed_variants:
                continue

            if rated_only:
                event = (headers.get("Event") or "").lower()
                if "rated" not in event:
                    continue

            if min_year is not None:
                y = parse_year(headers.get("UTCDate", ""))
                if y is None or y < min_year:
                    continue

            tc_cat = estimate_time_category(headers.get("TimeControl"))
            if allowed_timecats and (tc_cat not in allowed_timecats):
                continue

            try:
                w_elo = int(headers.get("WhiteElo", 0))
                b_elo = int(headers.get("BlackElo", 0))
            except Exception:
                continue

            b = get_elo_bin(w_elo, b_elo)
            if b not in buffers or bin_full(b):
                continue

            if min_plies and game_ply_count(game) < min_plies:
                continue

            try:
                san = game.board().variation_san(game.mainline_moves())
                movetext_full = str(game).split("\n\n", maxsplit=1)[-1].strip()
            except Exception:
                continue

            if not can_add_player(b, white, black):
                continue

            core_row, text_row = build_game_rows(headers, san, movetext_full, site=site)

            buffers[b].append((core_row, text_row, white or "", black or ""))

            if len(buffers[b]) >= chunk_size_per_bin:
                yield from flush_bin(b)

        for b in elo_bins:
            if emitted_per_bin[b] < games_per_bin and buffers[b]:
                yield from flush_bin(b)

    print("Streaming selection finished.")
