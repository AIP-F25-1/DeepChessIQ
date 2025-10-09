import sys, json, time, argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[2]))

import chess.pgn
from typing import Optional

from DeepChessIQ.dataset.Data.ETL.db_connection import get_connection
from DeepChessIQ.dataset.Data.ETL.db_insert import insert_game
from DeepChessIQ.dataset.Data.ETL.row_builder import build_game_rows
from DeepChessIQ.dataset.Data.ETL.pgn_headers import read_game_headers_only

# ---------- checkpoint helpers ----------
def _ck_default(pgn_path: Path) -> Path:
    ck_dir = Path(__file__).parent / ".checkpoints"
    ck_dir.mkdir(parents=True, exist_ok=True)
    return ck_dir / (pgn_path.stem + ".resume.checkpoint.json")

def _ck_load(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _ck_save(path: Path, state: dict):
    state["saved_at"] = datetime.utcnow().isoformat() + "Z"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def _fp(p: Path) -> dict:
    try:
        st = p.stat()
        return {"size": st.st_size, "mtime": int(st.st_mtime)}
    except Exception:
        return {"size": None, "mtime": None}

# ---------- utils ----------
def _elo_bin100_from_headers(h: dict) -> Optional[int]:
    def _to_int(x): 
        try: return int(x)
        except: return None
    w = _to_int(h.get("WhiteElo"))
    b = _to_int(h.get("BlackElo"))
    if w is None and b is None:
        return None
    if w is None: avg = b
    elif b is None: avg = w
    else: avg = (w + b) // 2
    return (avg // 100) * 100 if avg is not None else None

def _elo_bin100_from_rows(core_row: dict) -> Optional[int]:
    w = core_row.get("white_elo"); b = core_row.get("black_elo")
    if w is None and b is None: return None
    if w is None: avg = int(b)
    elif b is None: avg = int(w)
    else: avg = (int(w) + int(b)) // 2
    return (avg // 100) * 100

def _counts_by_bin(conn) -> dict[int, int]:
    q = """
    SELECT
      (((ISNULL(white_elo, black_elo) + ISNULL(black_elo, white_elo)) / 2) / 100) * 100 AS elo_bin_100,
      COUNT(*) AS game_count
    FROM dbo.game_core
    GROUP BY (((ISNULL(white_elo, black_elo) + ISNULL(black_elo, white_elo)) / 2) / 100) * 100
    """
    d: dict[int, int] = {}
    with conn.cursor() as cur:
        cur.execute(q)
        for binv, cnt in cur.fetchall():
            if binv is not None:
                d[int(binv)] = int(cnt)
    return d

# ---------- main sequential ingest ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn", required=True, type=str, help="Path to (possibly huge) PGN")
    ap.add_argument("--site", default="lichess", choices=["lichess", "chesscom"])
    ap.add_argument("--batch-size", type=int, default=3000)
    ap.add_argument("--log-every", type=int, default=1000)
    ap.add_argument("--quota-per-bin", type=int, default=10000)
    ap.add_argument("--checkpoint", type=str, default=None)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    pgn_path = Path(args.pgn).expanduser().resolve()
    if not pgn_path.exists():
        raise SystemExit(f"PGN not found: {pgn_path}")

    ck_path = Path(args.checkpoint) if args.checkpoint else _ck_default(pgn_path)
    ck = _ck_load(ck_path)
    fingerprint = _fp(pgn_path)

    start_cookie = 0
    processed = inserted = duplicates = failed = skipped_quota = 0
    if ck and not args.reset and ck.get("pgn_path") == str(pgn_path) and ck.get("fingerprint") == fingerprint:
        start_cookie = int(ck.get("cookie", 0))
        processed    = int(ck.get("processed", 0))
        inserted     = int(ck.get("inserted", 0))
        duplicates   = int(ck.get("duplicates", 0))
        failed       = int(ck.get("failed", 0))
        skipped_quota= int(ck.get("skipped_quota", 0))
        print(f"Resuming at cookie={start_cookie:,} (processed={processed:,})")
    elif ck and not args.reset:
        print("Checkpoint file differs from PGN (size/mtime); starting fresh.")

    t0 = time.time()
    last_cookie = start_cookie

    try:
        with get_connection() as conn:
            per_bin_counts = _counts_by_bin(conn)
            print(f"Loaded {len(per_bin_counts)} existing bins.")

            with pgn_path.open("r", encoding="utf-8", errors="replace", newline="") as fp, conn.cursor() as cur:
                # resume
                if start_cookie:
                    fp.seek(start_cookie)

                # process headers first — skip SAN parse when bin is full
                while True:
                    pos_before = fp.tell()
                    got_any = False
                    for headers, cookie_after in read_game_headers_only(fp):
                        got_any = True
                        last_cookie = cookie_after

                        bin100 = _elo_bin100_from_headers(headers)
                        if bin100 is not None and per_bin_counts.get(bin100, 0) >= args.quota_per_bin:
                            skipped_quota += 1
                            processed += 1
                        else:
                            # need to parse full game now (single game from pos_before to cookie_after)
                            # rewind to start of this game
                            fp.seek(pos_before)
                            game = chess.pgn.read_game(fp)
                            if game is None:
                                continue

                            # build SAN and movetext
                            board = game.board()
                            sans = []
                            for mv in game.mainline_moves():
                                sans.append(board.san(mv)); board.push(mv)
                            san_str = " ".join(sans)
                            exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
                            movetext_full = game.accept(exporter)

                            # compute ply_count cheaply
                            ply_count = len(sans)

                            rows = build_game_rows(dict(game.headers), san_str, movetext_full, site=args.site, ply_count=ply_count)
                            if rows:
                                core_row, text_row = rows
                                try:
                                    pk = insert_game(cur, core_row, text_row)
                                    if pk:
                                        inserted += 1
                                        b = _elo_bin100_from_rows(core_row)
                                        if b is not None:
                                            per_bin_counts[b] = per_bin_counts.get(b, 0) + 1
                                    else:
                                        duplicates += 1
                                except Exception as e:
                                    failed += 1
                            else:
                                # malformed → count as failed
                                failed += 1

                            processed += 1

                        # commit/checkpoint/logging
                        if processed % args.batch_size == 0:
                            conn.commit()
                            _ck_save(ck_path, {
                                "pgn_path": str(pgn_path),
                                "fingerprint": fingerprint,
                                "cookie": last_cookie,
                                "processed": processed,
                                "inserted": inserted,
                                "duplicates": duplicates,
                                "failed": failed,
                                "skipped_quota": skipped_quota,
                                "elapsed_sec": round(time.time() - t0, 2),
                            })

                        if processed % args.log_every == 0:
                            print(f"Processed {processed:,} | +{inserted:,} | dup {duplicates:,} | fail {failed:,} | skip_quota {skipped_quota:,}")

                        # next game's starting pos
                        pos_before = fp.tell()

                    if not got_any:
                        break  # EOF

                conn.commit()

    except KeyboardInterrupt:
        print("\n⏹️ Interrupted — saving checkpoint.")
    finally:
        _ck_save(ck_path, {
            "pgn_path": str(pgn_path),
            "fingerprint": fingerprint,
            "cookie": last_cookie,
            "processed": processed,
            "inserted": inserted,
            "duplicates": duplicates,
            "failed": failed,
            "skipped_quota": skipped_quota,
            "elapsed_sec": round(time.time() - t0, 2),
        })
        print(f"Checkpoint saved → {ck_path}")
        print(f"✅ Inserted {inserted:,} | 🔁 Duplicates {duplicates:,} | 🚫 Failed {failed:,} | ⏭️ Skipped(quota) {skipped_quota:,}")
        print(f"⏱️  Elapsed {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
