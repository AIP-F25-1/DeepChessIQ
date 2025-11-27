import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPO  # noqa: F401  (ensures correct algo type)
from ai.rl_train.config_ppo_vs_stockfish import get_ppo_config
from ai.rl_train.env_stockfish import StockfishEnv
from ray.rllib.models import ModelCatalog
from ai.rl_train.masked_policy_model import MaskedChessPolicy

ModelCatalog.register_custom_model("masked_chess_policy", MaskedChessPolicy)

if __name__ == "__main__":
    ray.init()

    # Register the custom env with a name RLlib understands
    tune.register_env(
        "DeepChessVsStockfish-v0", lambda env_config: StockfishEnv(**env_config)
    )

    config = get_ppo_config()

    # Build the PPO algorithm from config
    algo = config.build()

    for i in range(1):
        result = algo.train()
        print(
            f"Iteration {i}: reward_mean={result.get('episode_reward_mean', 0.0):.3f}, "
            f"length_mean={result.get('episode_len_mean', 0.0):.1f}"
        )
        if i % 10 == 0:
            ckpt = algo.save(f"checkpoints/ppo_stockfish_{i}")
            print(f"Checkpoint saved at: {ckpt}")

    final_ckpt = algo.save("checkpoints/ppo_stockfish_final")
    print(f"Final checkpoint saved at: {final_ckpt}")

    algo.stop()
    ray.shutdown()
