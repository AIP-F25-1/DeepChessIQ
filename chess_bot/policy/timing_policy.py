import math
from typing import Dict

def _entropy(ps): return -sum(p*math.log(p+1e-12) for p in ps)

def decide_think_time(blend: Dict, prior: Dict,
                      base_ms: int = 250, max_ms: int = 1500,
                      entropy_gain_ms: int = 800,
                      use_cp_gap: bool = True, cp_gap_threshold: int = 20,
                      prior_mix: float = 0.2) -> int:
    cands = blend.get("candidates", [])
    if not cands: return base_ms

    ps = [c["p_final"] for c in cands if c.get("p_final") is not None]
    if not ps: return base_ms
    ent = _entropy(ps); ent_max = math.log(len(ps))
    ent_norm = (ent/ent_max) if ent_max>0 else 0.0

    # cp gap
    cps = sorted([c["score_cp"] for c in cands if c.get("score_cp") is not None], reverse=True)
    gap = (cps[0]-cps[1]) if len(cps)>=2 else 999

    ms = base_ms + int(ent_norm * entropy_gain_ms)
    if use_cp_gap and gap < cp_gap_threshold: ms = int(ms * 1.2)

    # optional nudge from prior mean_ms
    if prior.get("moves"):
        tot = sum(m.get("freq",0) for m in prior["moves"])
        if tot>0:
            wsum = sum(m.get("freq",0) for m in prior["moves"] if m.get("mean_ms") is not None)
            if wsum>0:
                mean = sum(m["freq"]*m["mean_ms"] for m in prior["moves"] if m.get("mean_ms") is not None) / wsum
                ms = int((1-prior_mix)*ms + prior_mix*mean)

    return max(base_ms, min(max_ms, ms))
