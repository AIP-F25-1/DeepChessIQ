#!/usr/bin/env python3
import json, csv
from pathlib import Path
from time import sleep
from typing import Any, Dict, List

import requests
import chess.pgn

ENGINE_URL = "http://127.0.0.1:8001/bestmove"
PGN_FILE = Path("ai/data/sample_game.pgn")
OUT_JSON = Path("ai/data/eval_trace_depth20.json")
OUT_CSV = Path("ai/data/eval_trace_depth20.csv")
SLEEP_BETWEEN = 0.05


def evaluate():
    if not PGN_FILE.exists():
        raise FileNotFoundError(f"PGN not found: {PGN_FILE}")

    with open(PGN_FILE, encoding="utf-8") as f:
        game = chess.pgn.read_game(f)

    board = game.board()
    header = {
        k: game.headers.get(k) for k in ["Event", "Site", "Date", "White", "Black"]
    }

    print(f"Loaded game: {header['Event']} — {header['White']} vs {header['Black']}")
    print("=" * 70)

    trace: Dict[str, Any] = {
        "header": header,
        "mode": "depth",
        "depth": 20,
        "plies": [],
    }
    rows: List[List[Any]] = [
        [
            "ply",
            "move_no",
            "side",
            "san",
            "uci",
            "fen_after",
            "engine_reply_uci",
            "eval_type",
            "eval_value_cp",
            "elapsed_ms",
        ]
    ]

    for idx, move in enumerate(game.mainline_moves(), 1):
        san = board.san(move)
        uci = move.uci()
        move_no = (idx + 1) // 2
        side = "white" if (idx % 2 == 1) else "black"
        prefix = f"{move_no}. " if side == "white" else f"{move_no}... "

        board.push(move)
        fen_after = board.fen()

        r = requests.post(ENGINE_URL, json={"fen": fen_after, "depth": 20}, timeout=60)
        r.raise_for_status()
        data = r.json()

        eval_info = data.get("eval") or {}
        used = data.get("used") or {}
        engine_reply = data.get("uci")

        print(
            f"[{idx:02d}] {prefix}{san:<6} | eval: {eval_info.get('value')} {eval_info.get('type')} "
            f"| engine_reply: {engine_reply} | time: {used.get('elapsed_ms')} ms | depth={used.get('depth')}"
        )

        trace["plies"].append(
            {
                "ply": idx,
                "move_no": move_no,
                "side": side,
                "san": san,
                "uci": uci,
                "fen_after": fen_after,
                "engine_reply_uci": engine_reply,
                "eval_type": eval_info.get("type"),
                "eval_value_cp": eval_info.get("value"),
                "elapsed_ms": used.get("elapsed_ms"),
                "depth": used.get("depth"),
            }
        )

        rows.append(
            [
                idx,
                move_no,
                side,
                san,
                uci,
                fen_after,
                engine_reply,
                eval_info.get("type"),
                eval_info.get("value"),
                used.get("elapsed_ms"),
            ]
        )

        sleep(SLEEP_BETWEEN)

    print("=" * 70)
    print("Finished evaluating complete PGN at depth=20.")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"Saved JSON → {OUT_JSON}")
    print(f"Saved CSV  → {OUT_CSV}")


if __name__ == "__main__":
    evaluate()
