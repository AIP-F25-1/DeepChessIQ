import math
from typing import Dict, List, Optional

def _normalize(xs: List[float]) -> List[float]:
    s = sum(xs)
    return [x/s for x in xs] if s > 0 else [1.0/len(xs)] * len(xs)

def _softmax_cp(cps: List[Optional[int]], tau_cp: float = 60.0) -> List[float]:
    vals = [(cp if cp is not None else -10**9) / max(tau_cp, 1e-6) for cp in cps]
    m = max(vals)
    exps = [math.exp(v - m) for v in vals]
    return _normalize(exps)

def _temper(probs: List[float], T: float) -> List[float]:
    if T <= 1e-6:  # argmax
        out = [0.0]*len(probs); out[max(range(len(probs)), key=lambda i: probs[i])] = 1.0; return out
    xs = [p ** (1.0 / T) for p in probs]
    return _normalize(xs)

def blend_policy(engine_top: Dict, prior: Dict,
                 prior_weight: float = 0.6,
                 blunder_clamp_cp: int = 300,
                 temperature: float = 0.7) -> Dict:
    fen = engine_top["fen"]
    emoves = list(engine_top.get("top_moves", []))
    notes = []

    # Mate overrides
    mates_plus = [m for m in emoves if (m.get("mate") or 0) > 0]
    if mates_plus:
        pick = min(mates_plus, key=lambda m: m["mate"])
        return {"fen": fen, "candidates": [], "picked": {"uci": pick["uci"], "reason": "mate_win", "notes": ["fastest_mate"]}}

    # Avoid immediate mated lines if any safe exists
    safe = [m for m in emoves if not ((m.get("mate") or 0) < 0)]
    if safe and len(safe) < len(emoves):
        emoves = safe; notes.append("avoid_mated_lines")

    # Blunder clamp (relative to best cp)
    finite = [m for m in emoves if m.get("score_cp") is not None]
    if finite:
        best_cp = max(m["score_cp"] for m in finite)
        filtered = [m for m in emoves if (m.get("score_cp") or -10**9) >= best_cp - blunder_clamp_cp]
        if filtered:
            if len(filtered) < len(emoves): notes.append("blunder_clamp")
            emoves = filtered

    if not emoves:  # extreme fallback
        emoves = engine_top.get("top_moves", [])[:1]; notes.append("fallback_top1")

    # Engine probs from cp
    p_engine = _softmax_cp([m.get("score_cp") for m in emoves])

    # Prior probs from freq
    prior_map = {m["uci"]: m["freq"] for m in prior.get("moves", [])}
    if prior.get("total", 0) > 0:
        freqs = [prior_map.get(m["uci"], 0.0) for m in emoves]
        p_prior = _normalize([f + 1e-9 for f in freqs])
    else:
        p_prior = [0.0] * len(emoves)

    # Fusion
    w = max(0.0, min(1.0, prior_weight))
    p_final = _normalize([ (pe ** (1.0 - w)) * ((pp if pp>0 else 1e-12) ** w)
                           for pe, pp in zip(p_engine, p_prior) ])
    p_final = _temper(p_final, temperature)

    # Pick argmax (deterministic for now)
    idx = max(range(len(p_final)), key=lambda i: p_final[i])
    picked = emoves[idx]["uci"]

    # Trace
    candidates = []
    for i, m in enumerate(emoves):
        candidates.append({
            "uci": m["uci"],
            "p_engine": round(p_engine[i], 6),
            "p_prior": round((p_prior[i] if p_prior else 0.0), 6),
            "p_final": round(p_final[i], 6),
            "score_cp": m.get("score_cp"),
            "mate": m.get("mate"),
        })

    return {"fen": fen, "candidates": candidates, "picked": {"uci": picked, "reason": "blend", "notes": notes}}
