import ray
from ray.rllib.algorithms.ppo import PPO
from .config_ppo_vs_stockfish import get_ppo_config

if __name__ == "__main__":
    ray.init()
    config = get_ppo_config()

    # Newer API name
    algo = config.build_algo(PPO)  # instead of config.build()

    for i in range(50):
        result = algo.train()
        print(
            f"Iteration {i}: reward_mean={result['episode_reward_mean']:.3f}, "
            f"length_mean={result['episode_len_mean']:.1f}"
        )

        # Save checkpoint every 10 iterations
        if i % 10 == 0:
            checkpoint_path = algo.save(f"checkpoints/ppo_stockfish_{i}")
            print(f"Checkpoint saved at: {checkpoint_path}")

    # Final save
    final_checkpoint = algo.save("checkpoints/ppo_stockfish_final")
    print(f"Final checkpoint saved at: {final_checkpoint}")

    # Cleanup
    algo.stop()
    ray.shutdown()
