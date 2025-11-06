from ray.rllib.algorithms.callbacks import DefaultCallbacks
from typing import Dict, Any
import numpy as np


class ChessCallbacks(DefaultCallbacks):
    def on_episode_end(
        self, *, worker, base_env, policies, episode, env_index, **kwargs
    ):
        # Log custom metrics
        episode.custom_metrics["game_length"] = episode.length
        episode.custom_metrics["final_reward"] = episode.total_reward

        # Extract game outcome from last info
        last_info = episode.last_info_for()
        if last_info:
            # Assume env sets "outcome" in info on terminal
            outcome = last_info.get("outcome", "unknown")
            episode.custom_metrics["outcome"] = outcome

            # Count W/D/L
            if outcome == "win":
                episode.custom_metrics["wins"] = 1
                episode.custom_metrics["draws"] = 0
                episode.custom_metrics["losses"] = 0
            elif outcome == "draw":
                episode.custom_metrics["wins"] = 0
                episode.custom_metrics["draws"] = 1
                episode.custom_metrics["losses"] = 0
            elif outcome == "loss":
                episode.custom_metrics["wins"] = 0
                episode.custom_metrics["draws"] = 0
                episode.custom_metrics["losses"] = 1
            else:
                episode.custom_metrics["wins"] = 0
                episode.custom_metrics["draws"] = 0
                episode.custom_metrics["losses"] = 0

            # Illegal move ratio
            illegal_count = last_info.get("illegal_moves", 0)
            episode.custom_metrics["illegal_move_ratio"] = illegal_count / max(
                episode.length, 1
            )

            # Mean cp delta (if shaping enabled)
            cp_deltas = last_info.get("cp_deltas", [])
            if cp_deltas:
                episode.custom_metrics["mean_cp_delta"] = np.mean(cp_deltas)
            else:
                episode.custom_metrics["mean_cp_delta"] = 0.0

    def on_train_result(self, *, algorithm, result: Dict[str, Any], **kwargs):
        # Log training progress
        print(f"Training iteration: {result['training_iteration']}")
        print(f"Mean reward: {result['episode_reward_mean']}")
        print(f"Mean episode length: {result['episode_len_mean']}")
