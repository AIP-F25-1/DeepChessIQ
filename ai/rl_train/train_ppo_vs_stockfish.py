import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPO
from ai.rl_train.config_ppo_vs_stockfish import get_ppo_config
from ai.rl_train.env_stockfish import StockfishEnv

if __name__ == "__main__":
    ray.init()

    # Register the custom env with a name RLlib understands
    tune.register_env(
        "DeepChessVsStockfish-v0", lambda env_config: StockfishEnv(**env_config)
    )

    config = get_ppo_config()

    # Legacy-compatible build (no build_algo on older RLlib)
    algo = config.build()  # RLlib knows it's PPO from PPOConfig

    for i in range(1):
        result = algo.train()
        print(
            f"Iteration {i}: reward_mean={result['episode_reward_mean']:.3f}, "
            f"length_mean={result['episode_len_mean']:.1f}"
        )
        if i % 10 == 0:
            ckpt = algo.save(f"checkpoints/ppo_stockfish_{i}")
            print(f"Checkpoint saved at: {ckpt}")

    final_ckpt = algo.save("checkpoints/ppo_stockfish_final")
    print(f"Final checkpoint saved at: {final_ckpt}")

    algo.stop()
    ray.shutdown()
