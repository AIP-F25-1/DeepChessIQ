import random
import math
from typing import List, Dict, Any


def choose_move(
    candidates: List[Dict[str, Any]],
    temperature: float,
    mistake_rate: float,
    blunder_cap_cp: int,
) -> str:
    if not candidates:
        raise ValueError("No candidates provided")
    if len(candidates) == 1:
        return candidates[0]["uci"]

    # Sort by cp descending (best first)
    candidates = sorted(candidates, key=lambda x: x.get("cp", 0), reverse=True)
    best_cp = candidates[0].get("cp", 0)

    # Optimal set: within 30cp of best
    optimal = [c for c in candidates if best_cp - c.get("cp", 0) <= 30]
    # Suboptimal: up to blunder_cap_cp worse
    suboptimal = [
        c
        for c in candidates
        if best_cp - c.get("cp", 0) <= blunder_cap_cp and c not in optimal
    ]

    if random.random() < mistake_rate and suboptimal:
        # Sample from suboptimal
        pool = suboptimal
    else:
        # Sample from optimal
        pool = optimal

    if not pool:
        pool = candidates  # Fallback

    # Softmax sampling
    scores = [c.get("cp", 0) for c in pool]
    if temperature == 0:
        # Greedy
        return pool[0]["uci"]
    else:
        # Softmax
        exp_scores = [math.exp(s / temperature) for s in scores]
        total = sum(exp_scores)
        probs = [e / total for e in exp_scores]
        chosen = random.choices(pool, weights=probs, k=1)[0]
        return chosen["uci"]
