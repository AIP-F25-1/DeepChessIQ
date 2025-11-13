import json
from datetime import datetime
from pathlib import Path
import chess
from stockfish_service import StockfishService, SHORTLIST_N

LOGS = Path("logs"); LOGS.mkdir(parents=True, exist_ok=True)
OUT = LOGS / "engine_calls.jsonl"

TEST_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 4",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w kq - 0 7",
    "8/8/8/8/8/6k1/5p2/6K1 w - - 0 1",
]

def check_legality(fen, moves):
    board = chess.Board(fen)
    legal = {m.uci() for m in board.legal_moves}
    for m in moves:
        assert m["uci"] in legal, f"Illegal move {m['uci']} for FEN {fen}"

def main():
    with StockfishService() as svc, OUT.open("a", encoding="utf-8") as logf:
        for fen in TEST_FENS:
            res = svc.get_top_moves(fen, n=SHORTLIST_N)
            check_legality(fen, res["top_moves"])
            logf.write(json.dumps({
                "ts": datetime.utcnow().isoformat()+"Z",
                "fen": fen,
                "n": SHORTLIST_N,
                "meta": res["meta"],
                "returned": len(res["top_moves"]),
                "top1": res["top_moves"][0] if res["top_moves"] else None
            }) + "\n")
            print(f"OK: {fen[:25]}... -> {len(res['top_moves'])} candidates, top1={res['top_moves'][0]['uci']}")

if __name__ == "__main__":
    main()
