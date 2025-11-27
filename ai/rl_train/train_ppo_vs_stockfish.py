# ai/rl_train/train_ppo_vs_stockfish.py
import argparse
import os
import threading

import ray
from ray.rllib.algorithms.ppo import PPOConfig

from ray.tune.registry import register_env

from ray.rllib.models import ModelCatalog
from fastapi import FastAPI
import uvicorn

from .config_ppo_vs_stockfish import get_ppo_config
from .env_stockfish import StockfishEnv
from .masked_policy_model import MaskedChessModel

# Global variable to store the latest training result
latest_result = None

# FastAPI app for training status
app = FastAPI(title="DeepChessIQ Training Status")


@app.get("/training_status")
def get_training_status():
    if latest_result is None:
        return {"status": "not_started"}
    return {
        "iteration": latest_result.get("training_iteration", 0),
        "episode_reward_mean": latest_result.get("episode_reward_mean", 0.0),
        "episode_len_mean": latest_result.get("episode_len_mean", 0.0),
        "timesteps_total": latest_result.get("timesteps_total", 0),
        "time_total_s": latest_result.get("time_total_s", 0.0),
    }


def start_status_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")


def create_env(env_config):
    return StockfishEnv(env_config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-iters", type=int, default=50)
    parser.add_argument("--debug-env", action="store_true")
    args = parser.parse_args()

    ray.init(ignore_reinit_error=True)

    # Register env + model
    register_env("DeepChessVsStockfish-v0", create_env)
    ModelCatalog.register_custom_model("masked_chess_model", MaskedChessModel)

    cfg: PPOConfig = get_ppo_config()
    if args.debug_env:
        cfg.env_config["debug"] = True

    algo = cfg.build()

    # Start the status server in a background thread
    server_thread = threading.Thread(target=start_status_server, daemon=True)
    server_thread.start()

    for i in range(args.stop_iters):
        result = algo.train()
        global latest_result
        latest_result = result
        print(
            f"Iter {i}: "
            f"reward_mean={result['episode_reward_mean']:.3f}, "
            f"len_mean={result['episode_len_mean']:.2f}"
        )

        if (i + 1) % 10 == 0:
            chkpt = algo.save()
            print(f"Checkpoint saved at: {chkpt}")

    ray.shutdown()


if __name__ == "__main__":
    main()
