import hashlib

def hash_md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def hash_strict(headers: dict, san: str) -> str:
    """
    Hash includes exact names, elos, result, and SAN string.
    Used for exact duplicate checking.
    """
    key = f"{headers.get('White')}-{headers.get('Black')}-{headers.get('WhiteElo')}-{headers.get('BlackElo')}-{headers.get('Result')}-{san}"
    return hash_md5(key)

def hash_loose(headers: dict, san: str) -> str:
    """
    Hash ignores Elo fluctuations, only uses names, result, SAN.
    Used for deduping similar games.
    """
    key = f"{headers.get('White')}-{headers.get('Black')}-{headers.get('Result')}-{san}"
    return hash_md5(key)

def hash_meta_key(headers: dict) -> str:
    """
    Fingerprint to identify games from different sources.
    We'll use Date + Time + Player names + Elo diff.
    """
    dt = headers.get("UTCDate", "") + headers.get("UTCTime", "")
    white = headers.get("White", "")
    black = headers.get("Black", "")
    try:
        elo_diff = int(headers.get("WhiteElo", 0)) - int(headers.get("BlackElo", 0))
    except:
        elo_diff = 0
    key = f"{dt}-{white}-{black}-{elo_diff}"
    return hash_md5(key)[:24]  # 24 chars for meta_key_hash
