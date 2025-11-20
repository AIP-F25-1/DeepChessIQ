from ai.rl_train.env_stockfish import StockfishEnv
import numpy as np

env = StockfishEnv()  # respects .env (STOCKFISH_API, SF_MOVETIME_MS, etc.)
obs, info = env.reset()

for t in range(6):
    mask = info["action_mask"]
    legal = np.where(mask)[0]
    if legal.size == 0:
        print("No legal moves — episode ended.")
        break

    action = int(np.random.choice(legal))
    obs, reward, terminated, truncated, info = env.step(action)
    print(
        f"t={t} reward={reward:.3f} term={terminated} trunc={truncated} api_ms={info.get('api_ms')}"
    )

    if terminated or truncated:
        break

env.close()
print("Smoke OK.")
