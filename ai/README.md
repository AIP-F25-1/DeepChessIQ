# DeepChessIQ AI branch
This folder contains the AI work:
- engine/ : Stockfish service
- rlbot/  : RL environments + training
- data/   : local models/logs (ignored by git)

## Overview

This project connects a custom chess RL environment to a Stockfish FastAPI service and trains an agent with PPO using RLlib’s newer API. The sections below outline the main components.

---

## Custom Environment (`env_stockfish.py`)

- Talks to the Stockfish FastAPI service in `engine_service.py`.
- Builds 19-plane board observations.
- Uses a large discrete action space (about 4.8k moves).
- Returns an `action_mask` in the observation dict.
- Handles termination cases: resign, mate, draw.
- Applies a reward of -1 on illegal moves.

---

## Engine Microservice (`engine_service.py`)

- Exposes `/evaluate` and `/bestmove` endpoints.
- Typical latency is around 150 ms.
- Smoke tests confirm:
  - The env can step through positions.
  - Stockfish returns valid replies.
  - The environment resets cleanly.

---

## RL Driver (`train_ppo_vs_stockfish.py` + `config_ppo_vs_stockfish.py`)

- Registers the environment using RLlib’s new API.
- Builds the PPO config and runs training and evaluation loops.
- Sets up logging, checkpoints, and rollout workers.

---

## Callbacks (`rllib_callbacks.py`)

- Logs episode rewards, episode lengths, termination reasons, and ply counts.
- Already surfaced a key debugging signal:
  - Episodes ending at length 1.
  - Reward fixed at -1.
  - No Stockfish reply observed.

