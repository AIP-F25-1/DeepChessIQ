# rlbot-lc0 (Pretrained RL-style Bot)

A FastAPI microservice that wraps **lc0** (or Maia network) via UCI and exposes the **same session API** as our Stockfish service.

## Endpoints (contract mirrors Stockfish)
- `GET /ping` → `{ ok: true }`
- `GET /health` → `{ ready: boolean, detail?: string }`
- `POST /session?engine=rl&bot_id=<id>&temperature=0.5&mistake_rate=0.05&blunder_cap_cp=300`
  - Response: `{ session_id, fen, turn, history: [] }`
- `POST /session/{id}/move`
  - Request: `{ uci: "e2e4" }`
  - Response: `{ fen, history: [..., {user_move, bot_move, eval_like?}], turn }`
- `POST /session/{id}/resign` → `{ result: "0-1" | "1-0" | "1/2-1/2" }`
- (Optional) `POST /bestmove` → `{ uci, used: { movetime_ms }, eval_like? }`

### Persona params (query or body)
- `temperature` (0..1): higher = more variety
- `mistake_rate` (0..1): probability to select a suboptimal move
- `blunder_cap_cp` (int): max centipawn loss allowed for injected mistakes
- `movetime_ms` (override RL_MOVETIME_MS)

### Run locally
