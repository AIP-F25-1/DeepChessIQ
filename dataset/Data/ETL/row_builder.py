from datetime import datetime
from typing import Optional

from .utils_hashes import hash_loose, hash_strict, hash_meta_key

def parse_datetime(utc_date: str, utc_time: str) -> Optional[datetime]:
    try:
        return datetime.strptime(f"{utc_date} {utc_time}", "%Y.%m.%d %H:%M:%S")
    except Exception:
        return None

def build_game_rows(headers: dict, san: str, movetext_full: str, site: str = "lichess") -> tuple[dict, dict]:
    """
    Returns: (game_core_row, game_text_row)
    """

    site_url = headers.get("Site")
    site_game_id = site_url.split("/")[-1] if site_url else None

    white_elo = int(headers.get("WhiteElo", 0) or 0)
    black_elo = int(headers.get("BlackElo", 0) or 0)

    # Dates
    started_at = parse_datetime(headers.get("UTCDate", ""), headers.get("UTCTime", ""))
    date_only = started_at.date() if started_at else None

    # Hashes
    h_loose = hash_loose(headers, san)
    h_strict = hash_strict(headers, san)
    meta_hash = hash_meta_key(headers)

    core_row = {
        "site": site,
        "site_game_id": site_game_id,
        "site_url": site_url,

        "started_at_utc": started_at,
        "date_utc": date_only,

        "white_name": headers.get("White"),
        "black_name": headers.get("Black"),
        "white_elo": white_elo,
        "black_elo": black_elo,
        "white_rating_diff": int(headers.get("WhiteRatingDiff", 0) or 0),
        "black_rating_diff": int(headers.get("BlackRatingDiff", 0) or 0),

        "result": headers.get("Result"),
        "timecontrol": headers.get("TimeControl"),
        "eco": headers.get("ECO"),
        "opening": headers.get("Opening"),
        "termination": headers.get("Termination"),
        "variant": headers.get("Variant"),
        "round": headers.get("Round"),
        "ply_count": None,
        "start_fen": headers.get("FEN"),

        "hash_loose": h_loose,
        "hash_strict": h_strict,
        "meta_key_hash": meta_hash,
    }

    text_row = {
        "pgn_san": san,
        "pgn_movetext_full": movetext_full,
        "uci_seq": None,  # optional, for later
    }

    return core_row, text_row
