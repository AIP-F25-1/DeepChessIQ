import time
import numpy as np
from ai.rl_train.env_stockfish import StockfishEnv

if __name__ == "__main__":
    env = StockfishEnv(
        {"stockfish_api": "http://127.0.0.1:8001", "movetime_ms": 150, "use_shaping": 0}
    )
    obs, info = env.reset()
    for t in range(6):
        mask = info.get("action_mask", np.ones(4800, dtype=bool))
        legal_idxs = np.where(mask)[0]
        a = int(np.random.choice(legal_idxs)) if len(legal_idxs) else 0
        obs, r, term, trunc, info = env.step(a)
        print(
            f"t={t} reward={r:.3f} term={term} trunc={trunc} api_ms={info.get('api_ms', 0)}"
        )
        if term or trunc:
            break
    print("Smoke OK.") 
