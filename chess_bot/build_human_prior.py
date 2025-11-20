import os
import io
import re
import json
from collections import defaultdict

import pyodbc
import chess
import chess.pgn
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# ------------ Config from .env ------------
SQL_SERVER   = os.getenv("AZURE_SQL_SERVER")
SQL_DB       = os.getenv("AZURE_SQL_DB")
SQL_USER     = os.getenv("AZURE_SQL_USER")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")
SQL_DRIVER   = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
# Elo band (we’ll use elo_avg by default; you can switch to bin below)
ELO_MIN = int(os.getenv("PRIOR_ELO_MIN", "0"))
ELO_MAX = int(os.getenv("PRIOR_ELO_MAX", "9999"))
BIN_MIN = os.getenv("PRIOR_ELO_BIN_MIN")
BIN_MAX = os.getenv("PRIOR_ELO_BIN_MAX")

# Output path (auto-suffix with elo band if you left default)
OUT_PATH    = os.getenv("PRIOR_OUT", "data/human_prior.json")
MAX_PLY     = int(os.getenv("PRIOR_MAX_PLY", "16"))
MIN_SAMPLES = int(os.getenv("PRIOR_MIN_SAMPLES", "3"))
TOP_K       = int(os.getenv("PRIOR_TOP_K", "5"))
BATCH_LIMIT = int(os.getenv("PRIOR_BATCH_LIMIT", "20000"))

# auto-suffix output if using default and elo min/max are set
if OUT_PATH == "data/human_prior.json" and ELO_MIN and ELO_MAX:
    base, ext = os.path.splitext(OUT_PATH)
    OUT_PATH = f"{base}_elo{ELO_MIN}_{ELO_MAX}{ext}"

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

# ------------ Helpers: timecontrol & clocks ------------
TC_RE  = re.compile(r"^\s*(\d+)(?:\+(\d+))?\s*$")
CLK_RE = re.compile(r"\[\s*%clk\s+([0-9:]+)\s*\]")

def parse_timecontrol(tc_str: str):
    if not tc_str:
        return None, None
    m = TC_RE.match(tc_str.strip())
    if not m:
        return None, None
    base_s = int(m.group(1))
    inc_s  = int(m.group(2) or 0)
    return base_s*1000, inc_s*1000

def clock_to_ms(clk_str: str):
    if not clk_str:
        return None
    parts = [int(p) for p in clk_str.split(":")]
    if len(parts) == 2:
        hh, mm, ss = 0, parts[0], parts[1]
    elif len(parts) == 3:
        hh, mm, ss = parts
    else:
        return None
    return ((hh*60 + mm)*60 + ss) * 1000

def build_pgn_text(start_fen: str, movetext_full: str) -> str:
    headers = [
        '[Event "-"]','[Site "-"]','[Date "????.??.??"]','[Round "-"]',
        '[White "-"]','[Black "-"]','[Result "*"]','[SetUp "1"]', f'[FEN "{start_fen}"]'
    ]
    body = movetext_full.strip()
    if not body.endswith(("1-0","0-1","1/2-1/2","*")):
        body += " *"
    return "\n".join(headers) + "\n\n" + body + "\n"

def iter_plies_with_clocks(start_fen: str, movetext_full: str, timecontrol: str):
    base_ms, inc_ms = parse_timecontrol(timecontrol or "")
    pgn_text = build_pgn_text(start_fen, movetext_full)
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return
    board = game.board()
    prev_post_clk = {True: None, False: None}
    ply = 0
    for node in game.mainline():
        if node.move is None:
            continue
        fen_before = board.fen()
        side = board.turn
        san  = board.san(node.move)
        uci  = node.move.uci()
        board.push(node.move)
        ply += 1
        if MAX_PLY and ply > MAX_PLY:
            break
        post_ms = None
        if node.comment:
            m = CLK_RE.search(node.comment)
            if m:
                post_ms = clock_to_ms(m.group(1))
        think_ms = None
        if post_ms is not None:
            pre_ms = None
            if base_ms is not None:
                prev = prev_post_clk[side]
                pre_ms = base_ms if prev is None else max(prev + (inc_ms or 0), 0)
            if pre_ms is not None:
                delta = pre_ms - post_ms
                if 0 <= delta <= 10*60*1000:
                    think_ms = delta
            prev_post_clk[side] = post_ms
        yield {
            "ply": ply,
            "fen_before": fen_before,
            "uci": uci,
            "san": san,
            "side_to_move": "w" if side else "b",
            "post_clock_ms": post_ms,
            "think_ms": think_ms,
        }

class PriorAgg:
    def __init__(self):
        self.freq   = defaultdict(int)
        self.tt_sum = defaultdict(int)
        self.tt_cnt = defaultdict(int)
    def add(self, fen: str, uci: str, think_ms):
        k = (fen, uci)
        self.freq[k] += 1
        if think_ms is not None:
            self.tt_sum[k] += think_ms
            self.tt_cnt[k] += 1
    def to_compact(self, min_samples=3, top_k=5):
        by_fen = defaultdict(list)
        for (fen, uci), f in self.freq.items():
            if f < min_samples:
                continue
            mean_ms = int(self.tt_sum[(fen, uci)] / self.tt_cnt[(fen, uci)]) if self.tt_cnt[(fen, uci)] else None
            by_fen[fen].append({"uci": uci, "freq": f, "mean_ms": mean_ms, "n": f})
        out = {}
        for fen, moves in by_fen.items():
            moves.sort(key=lambda m: (-m["freq"], m["uci"]))
            sel = moves[:top_k] if top_k else moves
            out[fen] = {"fen": fen, "moves": sel, "total": sum(m["freq"] for m in sel)}
        return out

def connect_sql():
    conn_str = (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DB};"
        f"UID={SQL_USER};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, autocommit=False)

def fetch_rows(cursor, offset, limit):
    """
    Filter by elo band.
    Default: elo_avg BETWEEN ELO_MIN AND ELO_MAX.
    If PRIOR_ELO_BIN_MIN/MAX are set, we filter on elo_bin_100 instead.
    """
    use_bin = BIN_MIN is not None and BIN_MAX is not None
    if use_bin:
        # Ensure ints
        bin_min = int(BIN_MIN)
        bin_max = int(BIN_MAX)
        where_elo = f"core.elo_bin_100 BETWEEN {bin_min} AND {bin_max}"
    else:
        where_elo = f"core.elo_avg BETWEEN {ELO_MIN} AND {ELO_MAX}"

    q = f"""
    WITH t AS (
      SELECT
        core.game_pk,
        COALESCE(NULLIF(core.start_fen,''),'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') AS start_fen,
        COALESCE(core.timecontrol,'') AS timecontrol,
        txt.pgn_movetext_full
      FROM dbo.game_core AS core
      JOIN dbo.game_text  AS txt
        ON txt.game_pk = core.game_pk
      WHERE txt.pgn_movetext_full IS NOT NULL
        AND {where_elo}
    )
    SELECT * FROM t
    ORDER BY game_pk
    OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY;
    """
    cursor.execute(q)
    cols = [c[0] for c in cursor.description]
    for row in cursor:
        yield dict(zip(cols, row))

def build_human_prior():
    agg = PriorAgg()
    total, bad = 0, 0
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    with connect_sql() as conn:
        cur = conn.cursor()
        # Estimate count (optional)
        try:
            if BIN_MIN is not None and BIN_MAX is not None:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.game_core AS core
                    JOIN dbo.game_text AS txt ON txt.game_pk = core.game_pk
                    WHERE txt.pgn_movetext_full IS NOT NULL
                      AND core.elo_bin_100 BETWEEN ? AND ?;
                """, (int(BIN_MIN), int(BIN_MAX)))
            else:
                cur.execute("""
                    SELECT COUNT(*)
                    FROM dbo.game_core AS core
                    JOIN dbo.game_text AS txt ON txt.game_pk = core.game_pk
                    WHERE txt.pgn_movetext_full IS NOT NULL
                      AND core.elo_avg BETWEEN ? AND ?;
                """, (ELO_MIN, ELO_MAX))
            est = cur.fetchone()[0]
        except Exception:
            est = None

        offset = 0
        pbar = tqdm(total=est, desc=f"Scanning games (Elo {BIN_MIN or ELO_MIN}-{BIN_MAX or ELO_MAX})",
                    disable=(est is None))

        while True:
            batch = list(fetch_rows(cur, offset, BATCH_LIMIT))
            if not batch:
                break
            for rec in batch:
                total += 1
                movetext = rec["pgn_movetext_full"]
                if not movetext or len(movetext) < 8:
                    continue
                try:
                    for ply_item in iter_plies_with_clocks(rec["start_fen"], movetext, rec["timecontrol"]):
                        agg.add(ply_item["fen_before"], ply_item["uci"], ply_item["think_ms"])
                except Exception:
                    bad += 1
                    continue
                if est is not None:
                    pbar.update(1)
            offset += len(batch)

        if est is not None:
            pbar.close()

    prior = agg.to_compact(min_samples=MIN_SAMPLES, top_k=TOP_K)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(prior, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[OK] Wrote {len(prior)} FEN entries to {OUT_PATH}")
    print(f"Processed games: {total}, skipped/failed: {bad}")

if __name__ == "__main__":
    build_human_prior()
