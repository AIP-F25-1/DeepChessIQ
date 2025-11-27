# ai/rl_train/rllib_callbacks.py
from typing import Dict, Any

from ray.rllib.algorithms.callbacks import DefaultCallbacks


class ChessCallbacks(DefaultCallbacks):
    def on_episode_end(self, *, worker, base_env, policies, episode, **kwargs):
        info = episode.last_info_for()
        if not info:
            return

        outcome = info.get("outcome", "unknown")
        term = info.get("termination", "none")
        ply = info.get("ply_count", 0)
        illegal = info.get("illegal_moves", 0)

        episode.custom_metrics["ply_count"] = ply
        episode.custom_metrics["illegal_moves"] = illegal
        episode.custom_metrics[f"outcome_{outcome}"] = 1.0
        episode.custom_metrics[f"term_{term}"] = 1.0

        # Simple debug print
        print(
            f"[EPISODE] reward={episode.total_reward:.2f} len={episode.length} "
            f"outcome={outcome} term={term} ply={ply} illegal={illegal}"
        )
