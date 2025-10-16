# dataset/Data/ETL/load_pgn_parallel.py
from __future__ import annotations

import sys, json, time, argparse, multiprocessing as mp
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple, List

# allow `python -m DeepChessIQ...` from the parent folder
sys.path.append(str(Path(__file__).resolve().parents[2]))

from DeepChessIQ.dataset.Data.ETL.db_connection import get_connection
from DeepChessIQ.dataset.Data.ETL.row_builder import build_game_rows
from DeepChessIQ.dataset.Data.ETL.pgn_headers import read_game_headers_only

# -------------------- checkpoint helpers --------------------
def _ck_default(pgn_path: Path) -> Path:
    ck_dir = Path(__file__).parent / ".checkpoints"
    ck_dir.mkdir(parents=True, exist_ok=True)
    return ck_dir / (pgn_path.stem + ".parallel.checkpoint.json")

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

# -------------------- DB helpers --------------------
def counts_by_bin(conn) -> Dict[int, int]:
    q = "SELECT elo_bin_100, COUNT(*) FROM dbo.game_core GROUP BY elo_bin_100"
    d: Dict[int, int] = {}
    with conn.cursor() as cur:
        cur.execute(q)
        for binv, cnt in cur.fetchall():
            if binv is not None:
                d[int(binv)] = int(cnt)
    return d

def count_lt1500(conn) -> int:
    q = "SELECT COUNT(*) FROM dbo.game_core WHERE elo_bin_100 < 1500"
    with conn.cursor() as cur:
        cur.execute(q)
        row = cur.fetchone()
        return int(row[0] if row and row[0] is not None else 0)

def ensure_staging_tables(conn):
    """
    Create staging tables if missing. Stage text gets stage_id NULLable + hash_loose.
    """
    sql = """
IF OBJECT_ID('dbo._stage_game_core') IS NULL
BEGIN
  CREATE TABLE dbo._stage_game_core (
    stage_id           INT IDENTITY(1,1) PRIMARY KEY,
    hash_loose         CHAR(32)       NOT NULL,
    hash_strict        CHAR(32)       NOT NULL,
    meta_key_hash      CHAR(24)       NULL,
    site               NVARCHAR(16)   NOT NULL,
    site_game_id       NVARCHAR(32)   NULL,
    site_url           NVARCHAR(256)  NULL,
    started_at_utc     DATETIME2(7)   NULL,
    date_utc           DATE           NULL,
    white_name         NVARCHAR(64)   NULL,
    black_name         NVARCHAR(64)   NULL,
    white_elo          INT            NULL,
    black_elo          INT            NULL,
    white_rating_diff  INT            NULL,
    black_rating_diff  INT            NULL,
    result             NVARCHAR(7)    NULL,
    timecontrol        NVARCHAR(32)   NULL,
    eco                NVARCHAR(3)    NULL,
    opening            NVARCHAR(512)  NULL,
    termination        NVARCHAR(40)   NULL,
    variant            NVARCHAR(40)   NULL,
    round              NVARCHAR(16)   NULL,
    ply_count          INT            NULL,
    start_fen          NVARCHAR(200)  NULL
  );
END;

IF OBJECT_ID('dbo._stage_game_text') IS NULL
BEGIN
  CREATE TABLE dbo._stage_game_text (
    stage_id           INT            NULL,       -- NULLable; aligned post-insert if needed
    hash_loose         CHAR(32)       NULL,       -- join text by hash to inserted cores
    uci_seq            NVARCHAR(MAX)  NULL,
    pgn_san            NVARCHAR(MAX)  NULL,
    pgn_movetext_full  NVARCHAR(MAX)  NULL
  );
END;
"""
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()

# -------------------- Elo / bin helpers --------------------
def _to_int(x) -> Optional[int]:
    try: return int(x)
    except Exception: return None

def elo_bin100_from_headers(h: Dict[str, str]) -> Optional[int]:
    w = _to_int(h.get("WhiteElo")); b = _to_int(h.get("BlackElo"))
    if w is None and b is None: return None
    if w is None: avg = b
    elif b is None: avg = w
    else: avg = (w + b) // 2
    return (avg // 100) * 100 if avg is not None else None

def is_lt1500_from_bin(bin100: Optional[int]) -> bool:
    return bin100 is not None and bin100 < 1500

# NEW: compute bin from core row fields (no headers available at flush time)
def elo_bin100_from_core_row(row: Dict) -> Optional[int]:
    w = _to_int(row.get("white_elo"))
    b = _to_int(row.get("black_elo"))
    if w is None and b is None: return None
    if w is None: avg = b
    elif b is None: avg = w
    else: avg = (w + b) // 2
    return (avg // 100) * 100 if avg is not None else None

# -------------------- set-based batch flush --------------------
def flush_batch_set_based(conn, batch_core: List[dict], batch_text: List[dict]) -> Tuple[int, int, int]:
    """
    Bulk-insert using staging tables with in-batch de-duplication by hash_loose.
    Returns: (inserted_count, duplicate_count, inserted_lt1500_count)
    """
    if not batch_core:
        return (0, 0, 0)

    core_cols = [
        "hash_loose","hash_strict","meta_key_hash","site","site_game_id","site_url",
        "started_at_utc","date_utc","white_name","black_name","white_elo","black_elo",
        "white_rating_diff","black_rating_diff","result","timecontrol","eco","opening",
        "termination","variant","round","ply_count","start_fen"
    ]
    # stage text includes hash_loose so we can join by hash
    text_cols = ["stage_id","hash_loose","uci_seq","pgn_san","pgn_movetext_full"]

    inserted = 0
    dup = 0
    inserted_lt1500 = 0

    with conn.cursor() as cur:
        try:
            cur.timeout = 90
            cur.execute("SET LOCK_TIMEOUT 15000;")  # ms
        except Exception:
            pass

        # 1) Clear staging
        cur.execute("TRUNCATE TABLE dbo._stage_game_text;")
        cur.execute("TRUNCATE TABLE dbo._stage_game_core;")

        # 2) executemany into staging (fast_executemany ON)
        cur.fast_executemany = True
        core_rows = [tuple(row.get(c) for c in core_cols) for row in batch_core]
        cur.executemany(
            f"INSERT INTO dbo._stage_game_core ({','.join(core_cols)}) VALUES ({','.join(['?']*len(core_cols))})",
            core_rows
        )
        text_rows = [(None, r.get("hash_loose"), r.get("uci_seq"), r.get("pgn_san"), r.get("pgn_movetext_full")) for r in batch_text]
        cur.executemany(
            f"INSERT INTO dbo._stage_game_text ({','.join(text_cols)}) VALUES ({','.join(['?']*len(text_cols))})",
            text_rows
        )

        # 3) Insert new cores with in-batch de-duplication (rn=1 per hash_loose)
        cur.execute("IF OBJECT_ID('tempdb..#map') IS NOT NULL DROP TABLE #map; CREATE TABLE #map(hash_loose CHAR(32) PRIMARY KEY, game_pk BIGINT);")
        cur.execute(f"""
        WITH src AS (
          SELECT {','.join('sc.'+c for c in core_cols)},
                 ROW_NUMBER() OVER (PARTITION BY sc.hash_loose ORDER BY sc.stage_id) AS rn
          FROM dbo._stage_game_core sc
        )
        INSERT INTO dbo.game_core ({','.join(core_cols)})
        OUTPUT inserted.hash_loose, inserted.game_pk INTO #map(hash_loose, game_pk)
        SELECT {','.join('src.'+c for c in core_cols)}
        FROM src
        WHERE src.rn = 1
          AND NOT EXISTS (SELECT 1 FROM dbo.game_core gc WHERE gc.hash_loose = src.hash_loose);
        """)

        # how many inserted this flush
        cur.execute("SELECT COUNT(*) FROM #map;")
        inserted = int(cur.fetchone()[0])
        # duplicates = number of DISTINCT hashes in this batch - inserted
        cur.execute("SELECT COUNT(DISTINCT hash_loose) FROM dbo._stage_game_core;")
        distinct_hashes = int(cur.fetchone()[0])
        dup = max(0, distinct_hashes - inserted)

        # 4) Insert one text row per inserted hash_loose (dedupe), and avoid PK clashes
        cur.execute("""
        ;WITH st_dedup AS (
            SELECT st.*,
                    ROW_NUMBER() OVER (PARTITION BY st.hash_loose ORDER BY st.stage_id) AS rn
            FROM dbo._stage_game_text st
            WHERE st.hash_loose IS NOT NULL
        )
        INSERT INTO dbo.game_text (game_pk, uci_seq, pgn_san, pgn_movetext_full)
        SELECT m.game_pk, st.uci_seq, st.pgn_san, st.pgn_movetext_full
        FROM st_dedup st
        JOIN #map m ON m.hash_loose = st.hash_loose
        WHERE st.rn = 1
        AND NOT EXISTS (SELECT 1 FROM dbo.game_text gt WHERE gt.game_pk = m.game_pk);
        """)

        # 5) Count how many inserted were < 1500
        cur.execute("""
        SELECT COUNT(*) 
        FROM dbo.game_core gc
        JOIN #map m ON m.game_pk = gc.game_pk
        WHERE gc.elo_bin_100 < 1500;
        """)
        row = cur.fetchone()
        inserted_lt1500 = int(row[0] if row and row[0] is not None else 0)

        cur.execute("DROP TABLE #map;")

    return inserted, dup, inserted_lt1500

# -------------------- worker process --------------------
def worker_proc(job_q: mp.Queue, out_q: mp.Queue, site: str):
    """
    Input job: (headers_dict, raw_text, cookie_after)
    Output:
      ("ok", core_row, text_row, cookie)
      ("skip", None, None, cookie)  # feeder quota skip
      ("err", str, cookie)
    """
    import io
    import chess.pgn

    while True:
        item = job_q.get()
        if item is None:
            out_q.put(("eof", None, None, None))
            return

        headers, raw_text, cookie = item
        try:
            game = chess.pgn.read_game(io.StringIO(raw_text))
            if game is None:
                out_q.put(("skip", None, None, cookie))
                continue

            board = game.board()
            sans = []
            for mv in game.mainline_moves():
                sans.append(board.san(mv)); board.push(mv)
            san_str = " ".join(sans)
            ply_count = len(sans)

            exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
            movetext_full = game.accept(exporter)

            rows = build_game_rows(dict(game.headers), san_str, movetext_full, site=site, ply_count=ply_count)
            if not rows:
                out_q.put(("skip", None, None, cookie))
                continue

            core_row, text_row = rows
            out_q.put(("ok", core_row, text_row, cookie))
        except Exception as e:
            out_q.put(("err", f"{type(e).__name__}: {e}", cookie))

# -------------------- feeder (sequential reader; header-first) --------------------
# MINIMAL CHANGE: accept inserted_counts so we can enforce live quota without DB hits.
def feeder_proc(pgn_path: Path, start_cookie: int, quota_per_bin: int,
                per_bin_counts_snapshot: Dict[int,int], inserted_counts, job_q: mp.Queue, out_q: mp.Queue):
    per_bin_counts = dict(per_bin_counts_snapshot)
    with pgn_path.open("r", encoding="utf-8", errors="replace", newline="") as fp:
        if start_cookie:
            fp.seek(start_cookie)

        pos_before = fp.tell()
        while True:
            got_any = False
            for headers, cookie_after in read_game_headers_only(fp):
                got_any = True
                bin100 = elo_bin100_from_headers(headers)
                total = per_bin_counts.get(bin100, 0) + (inserted_counts.get(bin100, 0) if bin100 is not None else 0)
                if bin100 is not None and total >= quota_per_bin:
                    out_q.put(("skip", None, None, cookie_after))  # writer will count as skipped
                else:
                    # read raw slice (pos_before..cookie_after) and enqueue
                    cur = fp.tell()
                    fp.seek(pos_before)
                    raw_len = cookie_after - pos_before
                    raw_text = fp.read(raw_len)
                    fp.seek(cur)
                    job_q.put((headers, raw_text, cookie_after))

                pos_before = fp.tell()

            if not got_any:
                break  # EOF

# -------------------- main (writer in main proc) --------------------

def fetch_existing_bin_counts(conn, min_bin=1500):
    """Fetch elo_bin_100 counts from DB where bin >= min_bin"""
    query = """
        SELECT elo_bin_100, COUNT(*) AS count
        FROM game_core
        WHERE elo_bin_100 >= ?
        GROUP BY elo_bin_100
    """
    cur = conn.cursor()
    cur.execute(query, min_bin)
    rows = cur.fetchall()
    # pyodbc returns tuples by default -> (elo_bin_100, count)
    out = {}
    for r in rows:
        try:
            binv, cnt = r[0], r[1]
        except (TypeError, IndexError):
            # if a row object supports attribute access, fallback
            binv = getattr(r, "elo_bin_100", None)
            cnt = getattr(r, "count", None)
        if binv is not None:
            out[int(binv)] = int(cnt)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn", required=True, type=str)
    ap.add_argument("--site", default="lichess", choices=["lichess", "chesscom"])
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
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
    inserted_lt1500 = 0

    if ck and not args.reset and ck.get("pgn_path") == str(pgn_path) and ck.get("fingerprint") == fingerprint:
        start_cookie      = int(ck.get("cookie", 0))
        processed         = int(ck.get("processed", 0))
        inserted          = int(ck.get("inserted", 0))
        duplicates        = int(ck.get("duplicates", 0))
        failed            = int(ck.get("failed", 0))
        skipped_quota     = int(ck.get("skipped_quota", 0))
        inserted_lt1500   = int(ck.get("inserted_lt1500", 0))
        print(f"Resuming at cookie={start_cookie:,} (processed={processed:,})")
    elif ck and not args.reset:
        print("Checkpoint differs from PGN (size/mtime); starting fresh.")

    t0 = time.time()
    last_cookie = start_cookie

    ctx = mp.get_context("spawn")
    job_q: mp.Queue = ctx.Queue(maxsize=4000)
    out_q: mp.Queue = ctx.Queue(maxsize=4000)

    # NEW: shared in-memory per-bin counters for this run
    inserted_counts = ctx.Manager().dict()
    bin_quota_snapshot: Dict[int, int] = {}
    quota_reached_logged = set()

    try:
        with get_connection() as conn:
            bin_counts = fetch_existing_bin_counts(conn)
            print(f"[Startup] Loaded existing bin counts from DB (≥1500):")
            for b, c in sorted(bin_counts.items()):
                print(f"  - Bin {b}: {c} games")

            ensure_staging_tables(conn)

            per_bin_counts = counts_by_bin(conn)
            db_lt1500_start = count_lt1500(conn)
            print(f"Loaded {len(per_bin_counts)} existing bins. DB <1500 total: {db_lt1500_start:,}")

            # start feeder (NOTE: pass inserted_counts)
            feeder = ctx.Process(
                target=feeder_proc,
                args=(pgn_path, start_cookie, args.quota_per_bin, per_bin_counts, inserted_counts, job_q, out_q),
                daemon=True,
            )
            feeder.start()

            # start workers
            workers = []
            for _ in range(args.workers):
                p = ctx.Process(target=worker_proc, args=(job_q, out_q, args.site), daemon=True)
                p.start()
                workers.append(p)

            # writer loop (single connection)
            with conn.cursor():
                feeder_alive = True
                batch_core: List[dict] = []
                batch_text: List[dict] = []

                def do_flush():
                    nonlocal inserted, duplicates, inserted_lt1500, batch_core, batch_text
                    if not batch_core:
                        return
                    ins, dup, ins_lt = flush_batch_set_based(conn, batch_core, batch_text)
                    inserted        += ins
                    duplicates      += dup
                    inserted_lt1500 += ins_lt

                    # update per-bin in-memory counters BEFORE clearing
                    for row in batch_core:
                        b = elo_bin100_from_core_row(row)
                        if b is not None:
                            inserted_counts[b] = inserted_counts.get(b, 0) + 1

                    batch_core.clear()
                    batch_text.clear()
                    conn.commit()

                def save_ck():
                    _ck_save(ck_path, {
                        "pgn_path": str(pgn_path),
                        "fingerprint": fingerprint,
                        "cookie": last_cookie,
                        "processed": processed,
                        "inserted": inserted,
                        "duplicates": duplicates,
                        "failed": failed,
                        "skipped_quota": skipped_quota,
                        "inserted_lt1500": inserted_lt1500,
                        "db_lt1500_start": db_lt1500_start,
                        "elapsed_sec": round(time.time() - t0, 2),
                        # NEW: persist latest snapshot + quota
                        "bin_quota_snapshot": bin_quota_snapshot,
                        "quota_per_bin": args.quota_per_bin,
                    })

                while True:
                    try:
                        msg, core_row, text_row, cookie = out_q.get(timeout=1.0)
                    except Exception:
                        msg = None

                    if msg is None:
                        if not feeder.is_alive() and feeder_alive:
                            feeder_alive = False
                            for _ in range(len(workers)):
                                job_q.put(None)
                        if not feeder_alive and all(not w.is_alive() for w in workers) and out_q.empty():
                            break
                        continue

                    if cookie is not None:
                        last_cookie = cookie

                    if msg == "eof":
                        continue
                    elif msg == "skip":
                        skipped_quota += 1
                    elif msg == "ok":
                        # map to staging schema (matches dbo.game_core/text)
                        core_mapped = {
                            "hash_loose":        core_row.get("hash_loose"),
                            "hash_strict":       core_row.get("hash_strict"),
                            "meta_key_hash":     core_row.get("meta_key_hash"),
                            "site":              core_row.get("site"),
                            "site_game_id":      core_row.get("site_game_id"),
                            "site_url":          core_row.get("site_url"),
                            "started_at_utc":    core_row.get("started_at_utc"),
                            "date_utc":          core_row.get("date_utc"),
                            "white_name":        core_row.get("white_name"),
                            "black_name":        core_row.get("black_name"),
                            "white_elo":         core_row.get("white_elo"),
                            "black_elo":         core_row.get("black_elo"),
                            "white_rating_diff": core_row.get("white_rating_diff"),
                            "black_rating_diff": core_row.get("black_rating_diff"),
                            "result":            core_row.get("result"),
                            "timecontrol":       core_row.get("timecontrol"),
                            "eco":               core_row.get("eco"),
                            "opening":           core_row.get("opening"),
                            "termination":       core_row.get("termination"),
                            "variant":           core_row.get("variant"),
                            "round":             core_row.get("round"),
                            "ply_count":         core_row.get("ply_count"),
                            "start_fen":         core_row.get("start_fen"),
                        }
                        text_mapped = {
                            "hash_loose":        core_row.get("hash_loose"),
                            "uci_seq":           (text_row or {}).get("uci_seq"),
                            "pgn_san":           (text_row or {}).get("pgn_san"),
                            "pgn_movetext_full": (text_row or {}).get("pgn_movetext_full"),
                        }
                        batch_core.append(core_mapped)
                        batch_text.append(text_mapped)

                        if len(batch_core) >= args.batch_size:
                            do_flush()
                            # refresh snapshot for checkpoint after a flush
                            all_bins = set(per_bin_counts) | set(inserted_counts.keys())
                            bin_quota_snapshot = {b: per_bin_counts.get(b,0) + inserted_counts.get(b,0) for b in all_bins}
                            save_ck()
                    elif msg == "err":
                        failed += 1
                        if failed <= 5:
                            print(f"[worker err #{failed}] {core_row} {text_row}")
                    else:
                        failed += 1

                    processed += 1
                    if processed % args.log_every == 0:
                        # compact live status appended to your existing line
                        all_bins = set(per_bin_counts) | set(inserted_counts.keys())
                        totals = {b: per_bin_counts.get(b,0) + inserted_counts.get(b,0) for b in all_bins}
                        full_bins = [b for b, t in totals.items() if t >= args.quota_per_bin]
                        # top 3 bins with most remaining (or just first 3 sorted by remaining desc)
                        remain_pairs = [(b, args.quota_per_bin - totals[b]) for b in all_bins if totals[b] < args.quota_per_bin]
                        remain_pairs.sort(key=lambda x: x[1], reverse=True)
                        remain_preview = ", ".join(f"{b}:{r}" for b, r in remain_pairs[:3]) if remain_pairs else "—"
                        # side-effect: update snapshot for checkpoint
                        bin_quota_snapshot = totals
                        # print once when a bin becomes newly full
                        for b in full_bins:
                            if b not in quota_reached_logged:
                                print(f"  🚫 Bin {b} reached quota ({totals[b]}/{args.quota_per_bin}); skipping further games for this bin.")
                                quota_reached_logged.add(b)

                        print(
                            f"Processed {processed:,} | +{inserted:,} (lt1500 +{inserted_lt1500:,}) | "
                            f"dup {duplicates:,} | fail {failed:,} | skip_quota {skipped_quota:,} | "
                            f"bins_full {len(full_bins)} | remain {remain_preview}"
                        )

                # final flush + checkpoint
                do_flush()
                all_bins = set(per_bin_counts) | set(inserted_counts.keys())
                bin_quota_snapshot = {b: per_bin_counts.get(b,0) + inserted_counts.get(b,0) for b in all_bins}
                save_ck()
                print("✅ Done. Checkpoint saved.")

    finally:
        try:
            if 'feeder' in locals():
                feeder.terminate()
        except Exception:
            pass
        if 'workers' in locals():
            for w in workers:
                try: w.terminate()
                except Exception: pass

if __name__ == "__main__":
    mp.freeze_support()  # Windows support
    main()
