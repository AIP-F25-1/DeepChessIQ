import os, json, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from chess_bot.engine.stockfish_service import StockfishService, SHORTLIST_N
from chess_bot.policy.human_prior_store import HumanPriorStore
from chess_bot.policy.blend_policy import blend_policy
from chess_bot.policy.timing_policy import decide_think_time

LOGS = Path("logs"); LOGS.mkdir(parents=True, exist_ok=True)
MOVES_LOG = LOGS / "moves.jsonl"

PRIOR_WEIGHT      = float(os.getenv("BLEND_PRIOR_WEIGHT", "0.6"))
BLUNDER_CLAMP_CP  = int(os.getenv("BLUNDER_CLAMP_CP", "300"))
POLICY_TEMPERATURE= float(os.getenv("POLICY_TEMPERATURE", "0.7"))
TIME_BASE_MS      = int(os.getenv("TIME_BASE_MS", "250"))
TIME_MAX_MS       = int(os.getenv("TIME_MAX_MS", "1500"))
TIME_ENTROPY_GAIN = int(os.getenv("TIME_ENTROPY_GAIN_MS", "800"))

class MoveAPI:
    def __init__(self, prior_store: HumanPriorStore):
        self.prior = prior_store
        self.svc = StockfishService(); self.svc.open()

    def close(self): self.svc.close()

    def pick_move(self, fen: str) -> dict:
        engine_top = self.svc.get_top_moves(fen, n=SHORTLIST_N)
        prior = self.prior.get_prior(fen)
        blend = blend_policy(engine_top, prior,
                             prior_weight=PRIOR_WEIGHT,
                             blunder_clamp_cp=BLUNDER_CLAMP_CP,
                             temperature=POLICY_TEMPERATURE)
        think_ms = decide_think_time(blend, prior,
                                     base_ms=TIME_BASE_MS, max_ms=TIME_MAX_MS,
                                     entropy_gain_ms=TIME_ENTROPY_GAIN)
        time.sleep(think_ms/1000.0)
        picked = blend["picked"]["uci"]
        rec = {"fen": fen, "engine_top": engine_top["top_moves"], "prior": prior,
               "blend": blend, "think_ms": think_ms, "picked": picked}
        with MOVES_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

if __name__ == "__main__":
    store = HumanPriorStore()
    api = MoveAPI(store)
    try:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        out = api.pick_move(fen)
        print("Picked:", out["picked"], "think_ms:", out["think_ms"])
    finally:
        api.close()
