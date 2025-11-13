import os, json
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
load_dotenv()

HUMAN_PRIOR_PATH = os.getenv("HUMAN_PRIOR_PATH", "data/human_prior_elo2200_2400.json")
HUMAN_PRIOR_MIN_SAMPLES = int(os.getenv("HUMAN_PRIOR_MIN_SAMPLES", "3"))
HUMAN_PRIOR_TOPK = int(os.getenv("HUMAN_PRIOR_TOPK", "5"))

class HumanPriorStore:
    def __init__(self, path: Optional[str] = None):
        p = Path(path or HUMAN_PRIOR_PATH)
        if not p.exists():
            raise FileNotFoundError(f"Human prior file not found at {p}")
        with p.open("r", encoding="utf-8") as f:
            self._data: Dict[str, Dict] = json.load(f)

    def get_prior(self, fen: str) -> Dict:
        rec = self._data.get(fen)
        if not rec:
            return {"fen": fen, "moves": [], "total": 0}
        # defensive filtering
        moves = [m for m in rec.get("moves", []) if m.get("freq", 0) >= HUMAN_PRIOR_MIN_SAMPLES]
        moves.sort(key=lambda m: (-m["freq"], m["uci"]))
        if HUMAN_PRIOR_TOPK:
            moves = moves[:HUMAN_PRIOR_TOPK]
        total = sum(m["freq"] for m in moves)
        return {"fen": fen, "moves": moves, "total": total}
