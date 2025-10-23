#!/usr/bin/env python3
# fetch_chesscom_top50_gm_pgn.py
"""
Fetches Chess.com top-50 *GM* usernames (from leaderboards) and downloads their monthly PGN archives,
merging everything into a single PGN file you can feed to load_pgn_parallel.py with --site chesscom.

Usage:
  python fetch_chesscom_top50_gm_pgn.py --out ./downloads/chesscom_top50_gm.pgn \
      --category blitz --max-months 6 --max-players 50
"""

import argparse, time, sys, os, re, json
from pathlib import Path
from urllib.parse import urlparse
import requests

LEADERBOARDS = "https://api.chess.com/pub/leaderboards"   # returns top 50 per category
UA = "deepchessiq-ingest/1.0 (contact: you@example.com)"   # be nice to their API

def get_json(url, session, retries=3, backoff=1.5):
    for i in range(retries):
        r = session.get(url, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 304:
            return None
        if r.status_code == 429:
            # rate limited, back off harder
            time.sleep(backoff * (i + 1) * 3)
            continue
        # retry for transient 5xx
        if 500 <= r.status_code < 600:
            time.sleep(backoff * (i + 1))
            continue
        r.raise_for_status()
    r.raise_for_status()

def get_text(url, session, retries=3, backoff=1.5):
    for i in range(retries):
        r = session.get(url, timeout=60)
        if r.status_code == 200:
            return r.text
        if r.status_code == 429:
            time.sleep(backoff * (i + 1) * 3)
            continue
        if 500 <= r.status_code < 600:
            time.sleep(backoff * (i + 1))
            continue
        r.raise_for_status()
    r.raise_for_status()

def top50_usernames(category: str, session) -> list[str]:
    """
    category: one of 'bullet','blitz','rapid','daily','chess960','bughouse' (leaderboards vary)
    We filter entries by title == 'GM' and return unique usernames (lowercased per API norm).
    """
    data = get_json(LEADERBOARDS, session)
    if not data or category not in data:
        raise SystemExit(f"Category '{category}' not found in leaderboards")
    lst = data[category]
    out = []
    for p in lst:
        # examples have keys: 'username','title', ...
        t = (p.get("title") or "").upper()
        u = (p.get("username") or "").lower()
        if t == "GM" and u:
            out.append(u)
    # ensure unique & preserve order
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            uniq.append(u); seen.add(u)
    return uniq

def list_player_archives(user: str, session) -> list[str]:
    url = f"https://api.chess.com/pub/player/{user}/games/archives"
    data = get_json(url, session)
    return data.get("archives", []) if data else []

def month_label_from_url(url: str) -> str:
    # e.g. https://api.chess.com/pub/player/hikaru/games/2024/12
    m = re.search(r"/games/(\d{4})/(\d{2})$", url)
    return f"{m.group(1)}-{m.group(2)}" if m else "unknown"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output merged PGN file")
    ap.add_argument("--category", default="blitz", help="leaderboard category: blitz|bullet|rapid|daily|chess960 (default: blitz)")
    ap.add_argument("--max-players", type=int, default=50, help="limit number of GM users (<=50)")
    ap.add_argument("--max-months", type=int, default=6, help="limit how many most-recent months per player (avoid huge downloads)")
    ap.add_argument("--sleep", type=float, default=0.5, help="sleep between requests (s) to be nice")
    args = ap.parse_args()

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Encoding": "gzip"})

    print(f"[1/4] Fetching leaderboards for category '{args.category}' ...")
    gms = top50_usernames(args.category, session)
    if args.max_players and len(gms) > args.max_players:
        gms = gms[:args.max_players]
    print(f"  → Found {len(gms)} GM usernames: {', '.join(gms[:10])}{' ...' if len(gms)>10 else ''}")

    # Open output PGN file (append mode to allow resuming)
    with out_path.open("a", encoding="utf-8") as OUT:
        for i, u in enumerate(gms, 1):
            print(f"[2/4] {i}/{len(gms)} {u}: listing archives ...")
            try:
                archives = list_player_archives(u, session)
            except Exception as e:
                print(f"  ! archives error for {u}: {e}")
                continue

            # take most recent N months
            archives = sorted(archives)[-args.max_months:]
            for j, month_url in enumerate(archives, 1):
                pgn_url = f"{month_url}/pgn"
                label = month_label_from_url(month_url)
                print(f"      [{j}/{len(archives)}] pulling {u} {label}")
                try:
                    pgn = get_text(pgn_url, session)
                except Exception as e:
                    print(f"        ! pgn error for {u} {label}: {e}")
                    continue
                if pgn and pgn.strip():
                    # Write as-is (already PGN). Add a newline separator.
                    OUT.write(pgn)
                    if not pgn.endswith("\n"):
                        OUT.write("\n")
                time.sleep(args.sleep)

    print(f"[4/4] Done. PGN written to: {out_path}")

if __name__ == "__main__":
    main()
