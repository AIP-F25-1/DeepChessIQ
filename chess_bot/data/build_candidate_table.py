import os, io, re, json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import pyodbc
import chess, chess.pgn
from dotenv import load_dotenv

from chess_bot.engine.stockfish_service import StockfishService, SHORTLIST_N
from chess_bot.policy.human_prior_store import HumanPriorStore

load_dotenv()

SQL_SERVER   = os.getenv("AZURE_SQL_SERVER")
SQL_DB       = os.getenv("AZURE_SQL_DB")
SQL_USER     = os.getenv("AZURE_SQL_USER")
SQL_PASSWORD = os.getenv("AZURE_SQL_PASSWORD")
SQL_DRIVER   = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")

ELO_MIN = int(os.getenv("PRIOR_ELO_MIN", "2200"))
ELO_MAX = int(os.getenv("PRIOR_ELO_MAX", "2400"))

OUT_PARQUET = os.getenv("CANDIDATE_OUT", "data/candidates_2200_2400.parquet")
MAX_POSITIONS = int(os.getenv("CANDIDATE_MAX_POS", "100000"))  # safety cap
KEEP_MAX_PLY = int(os.getenv("CANDIDATE_MAX_PLY", "60"))       # limit early plies

TC_RE  = re.compile(r"^\s*(\d+)(?:\+(\d+))?\s*$")
CLK_RE = re.compile(r"\[\s*%clk\s+([0-9:]+)\s*\]")

def clock_to_ms(clk: str) -> Optional[int]:
    if not clk: return None
    parts = [int(p) for p in clk.split(":")]
    if   len(parts)==2: h,m,s = 0, parts[0], parts[1]
    elif len(parts)==3: h,m,s = parts
    else: return None
    return ((h*60+m)*60+s)*1000

def parse_timecontrol(tc: str) -> Tuple[Optional[int], Optional[int]]:
    if not tc: return None, None
    m = TC_RE.match(tc.strip()); 
    if not m: return None, None
    base = int(m.group(1))*1000; inc = int(m.group(2) or 0)*1000
    return base, inc

def pgntxt(start_fen, movetext):
    headers = ['[Event "-"]','[Site "-"]','[Date "????.??.??"]','[Round "-"]',
               '[White "-"]','[Black "-"]','[Result "*"]','[SetUp "1"]', f'[FEN "{start_fen}"]']
    body = movetext.strip()
    if not body.endswith(("1-0","0-1","1/2-1/2","*")): body += " *"
    return "\n".join(headers) + "\n\n" + body + "\n"

def iter_plies(start_fen: str, movetext_full: str, timecontrol: str):
    base_ms, inc_ms = parse_timecontrol(timecontrol or "")
    game = chess.pgn.read_game(io.StringIO(pgntxt(start_fen, movetext_full)))
    if not game: return
    board = game.board()
    prev_post = {True: None, False: None}
    ply = 0
    for node in game.mainline():
        if node.move is None: continue
        fen_before = board.fen()
        side = board.turn
        uci = node.move.uci()
        san = board.san(node.move)
        board.push(node.move)
        ply += 1
        post_ms = None
        if node.comment:
            m = CLK_RE.search(node.comment)
            if m: post_ms = clock_to_ms(m.group(1))
        think_ms = None
        if post_ms is not None and base_ms is not None:
            pre = base_ms if prev_post[side] is None else max(prev_post[side] + (inc_ms or 0), 0)
            d = pre - post_ms
            if 0 <= d <= 10*60*1000: think_ms = d
        prev_post[side] = post_ms
        yield {"ply": ply, "fen": fen_before, "side": "w" if side else "b",
               "human_uci": uci, "human_san": san, "think_ms": think_ms}

def connect_sql():
    cs = (
        f"DRIVER={{{SQL_DRIVER}}};SERVER={SQL_SERVER};DATABASE={SQL_DB};UID={SQL_USER};PWD={SQL_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(cs)

def main():
    Path("data").mkdir(exist_ok=True, parents=True)
    store = HumanPriorStore()  # uses HUMAN_PRIOR_PATH
    svc = StockfishService(); svc.open()

    with connect_sql() as conn, conn.cursor() as cur:
        # stream rows in elo band
        cur.execute(f"""
            SELECT TOP {MAX_POSITIONS*2}
              core.game_pk,
              COALESCE(NULLIF(core.start_fen,''),'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') AS start_fen,
              COALESCE(core.timecontrol,'') AS timecontrol,
              txt.pgn_movetext_full
            FROM dbo.game_core core
            JOIN dbo.game_text txt ON txt.game_pk = core.game_pk
            WHERE txt.pgn_movetext_full IS NOT NULL
              AND core.elo_avg BETWEEN ? AND ?
            ORDER BY core.game_pk;
        """, (ELO_MIN, ELO_MAX))

        rows = cur.fetchall()

    recs: List[Dict] = []
    kept_positions = 0

    for r in rows:
        start_fen, tc, movetext = r.start_fen, r.timecontrol, r.pgn_movetext_full
        try:
            for pl in iter_plies(start_fen, movetext, tc):
                if pl["ply"] > KEEP_MAX_PLY: break
                fen, side, human_uci, think_ms = pl["fen"], pl["side"], pl["human_uci"], pl["think_ms"]

                # get engine shortlist (up to 20)
                eng = svc.get_top_moves(fen, n=SHORTLIST_N)["top_moves"]
                if not eng: continue

                # if human move not in shortlist, skip this position (simplest)
                uci_list = [m["uci"] for m in eng]
                if human_uci not in uci_list:
                    continue

                # prior lookup
                prior = store.get_prior(fen)
                freq_map = {m["uci"]: m["freq"] for m in prior.get("moves", [])}
                mean_map = {m["uci"]: m.get("mean_ms") for m in prior.get("moves", [])}
                total_freq = prior.get("total", 0) or 1
                # group meta
                group_id = f"{hash(fen)}:{kept_positions}"

                best_cp = max([m["score_cp"] for m in eng if m.get("score_cp") is not None], default=None)
                cp_list = [(-10**9 if m.get("score_cp") is None else m["score_cp"]) for m in eng]
                # entropy-ish softmax over cp
                cp_tau = 60.0
                exps = np.exp((np.array(cp_list) / cp_tau) - (np.max(np.array(cp_list))/cp_tau))
                pe = (exps / (exps.sum() or 1.0)).tolist()
                prior_probs = [(freq_map.get(u, 0)/total_freq) for u in uci_list]

                for rank, m in enumerate(eng):
                    uci = m["uci"]
                    recs.append({
                        "group_id": group_id,
                        "fen": fen,
                        "side": 1 if side=="w" else 0,
                        "uci": uci,
                        "label_choice": 1 if uci==human_uci else 0,

                        "cp": m.get("score_cp"),
                        "mate": m.get("mate"),
                        "depth": m.get("depth"),
                        "pv_len": len(m.get("pv","").split()) if m.get("pv") else 0,
                        "engine_soft_p": pe[rank],

                        "prior_freq": freq_map.get(uci, 0),
                        "prior_prob": prior_probs[rank],
                        "prior_mean_ms": mean_map.get(uci),

                        "human_think_ms": think_ms,
                        "ply": pl["ply"],
                        "legal_count": len(uci_list),
                        "cp_to_best": (None if (best_cp is None or m.get("score_cp") is None)
                                       else best_cp - m["score_cp"]),
                    })
                kept_positions += 1
                if kept_positions >= MAX_POSITIONS: break
        except Exception:
            continue
        if kept_positions >= MAX_POSITIONS: break

    df = pd.DataFrame.from_records(recs)
    Path(OUT_PARQUET).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"[OK] wrote {len(df)} rows to {OUT_PARQUET} across {kept_positions} positions (≈20x each)")

if __name__ == "__main__":
    main()
