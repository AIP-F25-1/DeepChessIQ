from ray.rllib.algorithms.callbacks import DefaultCallbacks
from typing import Dict, Any
import numpy as np


class ChessCallbacks(DefaultCallbacks):
    def on_episode_end(
        self, *, worker, base_env, policies, episode, env_index, **kwargs
    ):
        # Always useful
        episode.custom_metrics["game_length"] = episode.length
        episode.custom_metrics["final_reward"] = episode.total_reward

        last_info = episode.last_info_for()
        if not last_info:
            return

        # Outcome flags
        outcome = last_info.get("outcome", "unknown")
        episode.custom_metrics["wins"] = 1 if outcome == "win" else 0
        episode.custom_metrics["draws"] = 1 if outcome == "draw" else 0
        episode.custom_metrics["losses"] = 1 if outcome == "loss" else 0
        episode.custom_metrics["outcome_score"] = {"win": 1, "draw": 0, "loss": -1}.get(
            outcome, 0
        )

        # Termination kind (one-hot for easy means per iter)
        term = last_info.get("termination", "unknown")
        for k in [
            "checkmate",
            "stalemate",
            "repetition",
            "fifty_move",
            "insufficient",
            "unknown",
        ]:
            episode.custom_metrics[k] = 1 if term == k else 0

        # Ply count (explicit)
        episode.custom_metrics["ply_count"] = last_info.get("ply_count", episode.length)

        # Illegal move ratio (already tracked)
        illegal_count = last_info.get("illegal_moves", 0)
        episode.custom_metrics["illegal_move_ratio"] = illegal_count / max(
            episode.length, 1
        )

        # Mean cp delta (your shaping proxy; ok if empty)
        cp_deltas = last_info.get("cp_deltas", [])
        episode.custom_metrics["mean_cp_delta"] = (
            float(np.mean(cp_deltas)) if cp_deltas else 0.0
        )

        # Optional: useful to see scheduling/latency
        episode.custom_metrics["api_ms"] = last_info.get("api_ms", 0)
        episode.custom_metrics["sf_movetime_ms"] = last_info.get(
            "stockfish_movetime_ms", 0
        )
        episode.custom_metrics["played_as_white"] = last_info.get("played_as_white", 1)

    def on_train_result(self, *, algorithm, result: Dict[str, Any], **kwargs):
        cm = result.get("custom_metrics", {})

        def m(name, default=0.0):
            # In RLlib, aggregated custom metrics are exposed as '<name>_mean'
            return cm.get(f"{name}_mean", default)

        # Rates
        w, d, l = m("wins"), m("draws"), m("losses")
        # Normalize in case of rounding; but means of 0/1 flags already are rates
        win_rate, draw_rate, loss_rate = w, d, l

        # Termination breakdown
        mate = m("checkmate")
        stal = m("stalemate")
        rep = m("repetition")
        fty = m("fifty_move")
        insf = m("insufficient")

        # Length
        avg_ply = m("ply_count")
        # p10 not directly provided; avg + collapse rate is still helpful
        quick_collapse = (
            1.0 * (m("game_length") <= 2) if "game_length_mean" in cm else 0.0
        )

        illegal = m("illegal_move_ratio")
        mean_cp = m("mean_cp_delta")

        it = result["training_iteration"]
        rew = result.get("episode_reward_mean", 0.0)
        ln = result.get("episode_len_mean", 0.0)

        print(
            f"[Iter {it}] "
            f"W/D/L={win_rate:.2f}/{draw_rate:.2f}/{loss_rate:.2f} | "
            f"rew={rew:.3f} len={ln:.1f} | "
            f"avg_ply={avg_ply:.1f} | "
            f"ends: mate {mate:.2f}, stal {stal:.2f}, rep {rep:.2f}, 50m {fty:.2f}, insuff {insf:.2f} | "
            f"illegal={illegal:.3f} | meanΔcp={mean_cp:.2f}"
        )
