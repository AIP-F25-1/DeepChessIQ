import os
from ray.rllib.algorithms.ppo import PPOConfig
from .rllib_callbacks import ChessCallbacks


def get_ppo_config():
    cfg = PPOConfig()

    # Environment
    cfg.environment("DeepChessVsStockfish-v0")
    cfg.env_config = {
        "stockfish_api": os.getenv("STOCKFISH_API", "http://127.0.0.1:8001"),
        "movetime_ms": int(os.getenv("SF_MOVETIME_MS", 150)),
        "use_shaping": int(os.getenv("USE_SHAPING", 1)),
        "shaping_clip_cp": int(os.getenv("SHAPING_CLIP_CP", 50)),
        "randomize_player_color": bool(int(os.getenv("RANDOMIZE_COLOR", 0))),
    }

    # Model: custom masked policy over (8,8,19)
    cfg.model = {
        "custom_model": "masked_chess_policy",  # name register with ModelCatalog
        "custom_model_config": {
            # pass conv + MLP layout into the custom model
            "conv_filters": [
                [32, [3, 3], 1],  # -> 8x8x32
                [64, [3, 3], 1],  # -> 8x8x64
            ],
            "conv_activation": "relu",
            "post_fcnet_hiddens": [256, 256],
            "post_fcnet_activation": "relu",
        },
        # if your model shares layers between policy + value
        "vf_share_layers": True,
    }

    cfg.framework("torch")

    # Training
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
