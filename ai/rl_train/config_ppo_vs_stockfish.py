# ai/rl_train/config_ppo_vs_stockfish.py
import os

from ray.rllib.algorithms.ppo import PPOConfig

from .masked_policy_model import MaskedChessModel
from .rllib_callbacks import ChessCallbacks


def get_ppo_config():
    cfg = PPOConfig()

    # Environment
    cfg.environment(
        env="DeepChessVsStockfish-v0",
        env_config={
            "stockfish_api": os.getenv("STOCKFISH_API", "http://127.0.0.1:8001"),
            "movetime_ms": int(os.getenv("SF_MOVETIME_MS", 150)),
            "use_shaping": int(os.getenv("USE_SHAPING", 1)),
            "shaping_clip_cp": int(os.getenv("SHAPING_CLIP_CP", 50)),
            "randomize_player_color": bool(int(os.getenv("RANDOMIZE_COLOR", 0))),
            "debug": bool(int(os.getenv("ENV_DEBUG", "0"))),
        },
    )

    # Register custom model
    cfg.model.update(
        {
            "custom_model": "masked_chess_model",
            "custom_model_config": {},
        }
    )
    cfg.framework("torch")

    # Training hyperparams
    cfg.training(
        gamma=0.99,
        lr=5e-5,
        train_batch_size=2048,
        sgd_minibatch_size=256,
        num_sgd_iter=10,
        clip_param=0.2,
        vf_clip_param=10.0,
        entropy_coeff=0.01,
        vf_loss_coeff=0.5,
    )

    # Rollout
    cfg.rollouts(
        num_rollout_workers=2,
        num_envs_per_worker=2,
        rollout_fragment_length=64,
        batch_mode="truncate_episodes",
    )

    # Resources
    cfg.resources(num_gpus=0, num_cpus_per_worker=1)

    # Callbacks
    cfg.callbacks(ChessCallbacks)

    # Evaluation
    cfg.evaluation(
        evaluation_interval=5,
        evaluation_duration=10,
        evaluation_duration_unit="episodes",
        evaluation_config={"explore": False},
    )

    # Checkpointing
    cfg.checkpointing(export_native_model_files=True)

    return cfg
