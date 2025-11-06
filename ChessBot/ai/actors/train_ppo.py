# train_ppo.py
from __future__ import annotations
import os
from ray import air, tune
import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.models import ModelCatalog

from env_chess_rllib import ChessVsEngineEnv, ACTION_SPACE_SIZE, OBS_SIZE
import masking_model  # registers "masked_fc_policy"


def main():
    ray.init(ignore_reinit_error=True, include_dashboard=False)

    # Register env with RLlib
    tune.register_env("ChessVsEngineEnv", lambda cfg: ChessVsEngineEnv(cfg))

    # PPO configuration
    config = (
        PPOConfig()
        .environment(
            env="ChessVsEngineEnv",
            env_config={
                "agent_plays_white": True,
                "engine_k": 4,
                "movetime_ms": 80,            # faster for training rollouts
                "depth_cap": 0,
                "use_mock_engine": True,      # flip to False and set ENGINE_BIN to use Stockfish
                "engine_bin": os.getenv("ENGINE_BIN"),
            },
        )
        .framework("torch")
        .rollouts(
            num_rollout_workers=2,
            rollout_fragment_length=128,
            batch_mode="truncate_episodes",
        )
        .training(
            model={
                "custom_model": "masked_fc_policy",
                "fcnet_hiddens": [512, 256],
            },
            gamma=0.995,
            lr=3e-4,
            train_batch_size=32768,   # accumulated across workers
            sgd_minibatch_size=2048,
            num_sgd_iter=8,
            vf_clip_param=10.0,
            grad_clip=0.5,
            entropy_coeff=0.01,       # a bit of exploration
        )
        .resources(
            num_gpus=0
        )
    )

    algo = config.build()

    # Train a few iterations; increase as needed
    for i in range(10):
        result = algo.train()
        print(f"Iter {i}: reward_mean={result['episode_reward_mean']:.3f}, len_mean={result['episode_len_mean']:.1f}")

    # Save checkpoint
    ckpt = algo.save()
    print("Saved checkpoint to:", ckpt)

    ray.shutdown()


if __name__ == "__main__":
    main()
