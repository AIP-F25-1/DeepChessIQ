from ray.rllib.algorithms.ppo import PPOConfig
from .rllib_callbacks import ChessCallbacks
import os


def get_ppo_config():
    config = PPOConfig()

    # Environment (direct class path; no register() needed)
    config.environment(
        "ai.rl_train.env_stockfish:StockfishEnv",
        env_config={
            "stockfish_api": os.getenv("STOCKFISH_API", "http://127.0.0.1:8001"),
            "movetime_ms": int(os.getenv("SF_MOVETIME_MS", 150)),
            "use_shaping": int(os.getenv("USE_SHAPING", 0)),
            "shaping_clip_cp": int(os.getenv("SHAPING_CLIP_CP", 50)),
        },
    )

    # Model (new API)
    config.rl_module(
        model_config={"fcnet_hiddens": [256, 256], "fcnet_activation": "relu"}
    )

    config.training(
        gamma=0.995,
        lr=5e-4,
        clip_param=0.2,
        num_epochs=8,  # replaces num_sgd_iter
        minibatch_size=512,  # replaces sgd_minibatch_size
        train_batch_size=4096,
    )

    # New API: env_runners instead of rollouts()
    config.env_runners(
        num_env_runners=2,
        num_envs_per_env_runner=2,
        num_cpus_per_env_runner=1,
    )

    config.resources(num_gpus=0)
    config.framework("torch")

    config.evaluation(
        evaluation_interval=10,
        evaluation_duration=5,
        evaluation_config={"explore": False},
    )

    config.callbacks(ChessCallbacks)
    config.ignore_env_runner_failures = True
    return config
