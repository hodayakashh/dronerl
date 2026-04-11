# Architecture & Implementation Plan — DroneRL

## Project Structure

```
dronerl/
├── src/
│   └── dronerl/
│       ├── __init__.py              # Package entry, exports __version__
│       ├── constants.py             # Immutable project constants
│       ├── shared/
│       │   ├── version.py           # Version tracking (start: 1.00)
│       │   ├── config.py            # ConfigLoader — reads YAML/JSON
│       │   └── logger.py            # Centralized logging
│       ├── environment/
│       │   ├── __init__.py
│       │   ├── grid.py              # Grid data model & CellType enum
│       │   ├── wind.py              # Stochastic wind zone logic
│       │   ├── rewards.py           # RewardConfig + RewardCalculator
│       │   └── env.py               # SmartCityEnv: reset(), step()
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── q_table.py           # QTable wrapper (NumPy)
│       │   ├── policy.py            # EpsilonGreedyPolicy
│       │   └── agent.py             # Agent: select_action(), update()
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── renderer.py          # Pygame grid & sprite rendering
│       │   ├── heatmap.py           # Value heatmap overlay
│       │   ├── arrows.py            # Policy arrows overlay
│       │   ├── dashboard.py         # Real-time reward & epsilon graphs
│       │   └── level_editor.py      # Interactive level editor
│       ├── sdk.py                   # DroneRLSDK — single entry point
│       └── main.py                  # CLI entry point
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/
│   │   ├── test_grid.py
│   │   ├── test_wind.py
│   │   ├── test_rewards.py
│   │   ├── test_env.py
│   │   ├── test_q_table.py
│   │   ├── test_policy.py
│   │   ├── test_agent.py
│   │   └── test_sdk.py
│   └── integration/
│       └── test_training_loop.py
├── config/
│   ├── settings.yaml                # RL hyperparameters
│   ├── setup.json                   # App config (versioned)
│   ├── rate_limits.json             # API/resource rate limits
│   └── logging_config.json          # Logging configuration
├── docs/
│   ├── PRD.md
│   ├── PLAN.md
│   ├── TODO.md
│   ├── PRD_q_learning.md
│   └── PROMPTS.md
├── results/                         # Experiment outputs
├── assets/                          # Images, sprites, resources
├── notebooks/                       # Analysis notebooks
├── data/                            # Input data / saved Q-tables
├── logs/                            # Runtime logs (git-ignored)
├── README.md
├── pyproject.toml                   # Build, lint, test config
├── uv.lock                          # Locked dependencies
├── .env-example                     # Secret placeholders (committed)
├── .gitignore
└── main.py                          # Root launcher
```

## Milestone 1 — Project Structure & Configuration

### `pyproject.toml`
```toml
[project]
name = "dronerl"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "pygame>=2.5",
    "numpy>=1.26",
    "pyyaml>=6.0",
    "matplotlib>=3.8",
]

[project.optional-dependencies]
dev = ["pytest>=7.4", "pytest-cov>=4.1", "ruff>=0.3"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["src"]
omit = ["src/dronerl/main.py", "*/tests/*", "src/**/gui/*"]

[tool.coverage.report]
fail_under = 85
```

### `config/setup.json`
```json
{
  "version": "1.00",
  "app_name": "DroneRL",
  "grid": {"rows": 12, "cols": 12},
  "gui": {"fps": 60, "cell_size": 56, "window_title": "DroneRL — Smart City"}
}
```

### `config/rate_limits.json`
```json
{
  "version": "1.00",
  "rate_limits": {
    "default": {
      "requests_per_minute": 60,
      "concurrent_max": 4,
      "max_retries": 3
    }
  }
}
```

### `config/settings.yaml`
```yaml
agent:
  alpha: 0.1
  gamma: 0.95
  epsilon_start: 1.0
  epsilon_min: 0.01
  epsilon_decay: 0.995
  max_episodes: 3000
  max_steps: 200

rewards:
  step: -1
  goal: 100
  trap: -50
  wind: -2
  wall: -5

logging:
  level: INFO
  file: logs/dronerl.log
```

### `src/dronerl/shared/version.py`
```python
VERSION = "1.00"
```

### `src/dronerl/__init__.py`
```python
from dronerl.shared.version import VERSION
__version__ = VERSION
__all__ = ["__version__"]
```

### `src/dronerl/shared/config.py`
- Class `ConfigLoader`
- `load_yaml(path: str) -> SimpleNamespace` — reads YAML, validates required keys
- `load_json(path: str) -> dict` — reads JSON config
- Raises `ConfigError` on missing required fields

### `src/dronerl/shared/logger.py`
- `get_logger(name: str) -> logging.Logger`
- Reads level/file from `config/logging_config.json`
- Single `FileHandler` + `StreamHandler`

### `src/dronerl/constants.py`
```python
from enum import IntEnum

class Action(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

N_ACTIONS = len(Action)
```

### `.env-example`
```
# Copy to .env and fill in values
DRONERL_LOG_LEVEL=INFO
DRONERL_CONFIG_PATH=config/setup.json
```

### `.gitignore`
```
.env
logs/
__pycache__/
*.pyc
.coverage
htmlcov/
dist/
*.egg-info/
.venv/
uv.lock.bak
results/*.pkl
data/q_tables/*.npy
```

---

## Milestone 2 — Core RL Engine & Environment

### `src/dronerl/environment/grid.py`
- `CellType` enum: `EMPTY, WALL, TRAP, WIND, GOAL, START`
- `Grid` class
  - `__init__(rows, cols)` — allocates 2D list of `CellType`
  - `set_cell(r, c, cell_type)`
  - `get_cell(r, c) -> CellType`
  - `is_walkable(r, c) -> bool` — False for WALL only
  - `in_bounds(r, c) -> bool`
  - `load_from_dict(layout: dict)` — builds grid from config layout

### `src/dronerl/environment/wind.py`
- `WindZone` class
  - `__init__(drift_prob: float, rng: np.random.Generator)`
  - `apply(action: int) -> int` — returns possibly-deflected action
  - With prob `drift_prob`, picks one of the 3 other directions

### `src/dronerl/environment/rewards.py`
- `RewardConfig` dataclass: `step, goal, trap, wind, wall`
- `RewardCalculator`
  - `__init__(config: RewardConfig)`
  - `calculate(cell_type: CellType, was_wind: bool) -> float`

### `src/dronerl/environment/env.py`
- `SmartCityEnv`
  - `__init__(grid, wind, reward_calc, start, goal)`
  - `reset() -> tuple[int, int]`
  - `step(state, action) -> (next_state, reward, done)`
  - `_apply_action(state, action) -> tuple[int, int]`

### `src/dronerl/agent/q_table.py`
- `QTable`
  - `__init__(rows, cols, n_actions)` — zeros `(rows, cols, n_actions)` array
  - `get(r, c) -> np.ndarray`
  - `get_value(r, c, a) -> float`
  - `set_value(r, c, a, value: float)`
  - `best_action(r, c) -> int`
  - `max_value(r, c) -> float`

### `src/dronerl/agent/policy.py`
- `EpsilonGreedyPolicy`
  - `__init__(epsilon_start, epsilon_min, decay, n_actions, rng)`
  - `select(q_row: np.ndarray) -> int`
  - `decay_epsilon()`
  - `epsilon` property

### `src/dronerl/agent/agent.py`
- `Agent`
  - `__init__(q_table, policy, alpha, gamma)`
  - `select_action(state) -> int`
  - `update(state, action, reward, next_state, done)`
    - Bellman: `Q[s,a] += alpha * (r + gamma * max(Q[s']) - Q[s,a])`
  - `end_episode()`

---

## Milestone 3 — GUI, Overlays & Level Editor

### GUI Layout
```
┌─────────────────────────────────────┬──────────────────────┐
│                                     │  DroneRL Dashboard   │
│         GRID (12×12)                │  Episode: N          │
│         + Heatmap overlay           │  Total Reward: X     │
│         + Policy arrows overlay     │  Epsilon: X          │
│         + Drone sprite              │  Steps: X            │
│                                     │  Goal Rate: X%       │
│                                     │                      │
│                                     │  Reward History      │
│                                     │  [line graph]        │
│                                     │                      │
│                                     │  Legend:             │
│                                     │  □ Empty             │
│                                     │  □ Building          │
│                                     │  □ Trap              │
│                                     │  □ Goal              │
│                                     │  □ Wind Zone         │
├─────────────────────────────────────┴──────────────────────┤
│ Mode: Training [PAUSED]  [SPACE] Pause  [F] Fast  [W] Heatmap  [A] Arrows  [E] Editor  [S] Save  [L] Load  [R] Reset │
└────────────────────────────────────────────────────────────┘
```

### Keyboard Controls
| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume training |
| `F` | Toggle fast mode (skip rendering, max speed) |
| `W` | Toggle value heatmap overlay |
| `A` | Toggle policy arrows overlay |
| `E` | Open / close level editor |
| `S` | Save Q-table ("brain") to file |
| `L` | Load Q-table ("brain") from file |
| `R` | Hard reset (Q-table + epsilon + episode counter) |
| `ESC` | Quit |

### `src/dronerl/gui/renderer.py`
- `Renderer`
  - `__init__(grid, config)` — creates Pygame window; grid panel + dashboard panel
  - `draw_grid(drone_pos, episode, step, mode, paused)` — draws cells, drone, overlays
  - `draw_status_bar(mode, paused, show_heatmap, show_arrows)` — bottom bar with all key hints
  - `_cell_color(cell_type) -> tuple` — color per CellType
  - `_draw_drone(surface, pos)` — drone sprite (yellow crosshair)
  - `_draw_legend(surface)` — color legend panel
  - `clear()`, `flip()`

### `src/dronerl/gui/heatmap.py`
- `HeatmapOverlay`
  - `__init__(cell_size, rows, cols)`
  - `draw(surface, q_table, grid)` — orange/red gradient by max Q-value per cell
  - `_value_to_color(v, vmin, vmax) -> tuple` — maps value to RGB
  - Handle edge case: all zeros → uniform color
  - Handle edge case: vmin == vmax → uniform color

### `src/dronerl/gui/arrows.py`
- `ArrowOverlay`
  - `__init__(cell_size)`
  - `draw(surface, q_table, grid)` — directional arrow per non-wall cell
  - `_draw_arrow(surface, center, action, color)` — polygon arrow

### `src/dronerl/gui/dashboard.py`
- `Dashboard`
  - `__init__(config)` — right-side panel dimensions from config
  - `update(episode, total_reward, epsilon, steps, goal_rate, episode_rewards)`
  - `draw(surface)` — renders all dashboard elements:
    - Title: "DroneRL Dashboard"
    - Stats: Episode, Total Reward, Epsilon, Steps, Goal Rate %
    - Reward History graph (last 100 episodes, Pygame only)
    - Color legend for CellTypes
  - `_draw_graph(surface, data, rect, color)` — mini line graph helper

### `src/dronerl/gui/level_editor.py`
- `LevelEditor`
  - `__init__(renderer, grid)`
  - `run() -> Grid` — blocking event loop; overlays on top of current grid
  - Left-click: cycle cell type EMPTY → WALL → TRAP → WIND → GOAL → START
  - Right-click: reset cell to EMPTY
  - `S` key: save to `config/custom_level.yaml`
  - `R` key: reset entire grid
  - `ESC`: exit editor, return modified grid

---

## Milestone 4 — SDK & Main Loop

### `src/dronerl/sdk.py`
- `DroneRLSDK` — **single entry point for ALL business logic**
  - `__init__(config_path: str)`
  - `run_headless(n_episodes: int) -> list[float]`
  - `run_gui()`
  - `get_q_table() -> QTable`
  - `get_policy_map() -> dict[tuple, int]`
  - `save_q_table(path: str)`
  - `load_q_table(path: str)`
  - `launch_level_editor()`

**No business logic in GUI or CLI layers — all routes through SDK.**

### GUI Game Loop
```
while running:
    handle_events()
    action = agent.select_action(state)
    next_state, reward, done = env.step(state, action)
    agent.update(state, action, reward, next_state, done)
    state = next_state
    renderer.draw_grid(state, episode, step)
    if show_heatmap: heatmap.draw(screen, q_table)
    if show_arrows:  arrows.draw(screen, q_table, grid)
    dashboard.update(rewards, epsilons)
    dashboard.draw(screen)
    clock.tick(fps)
    if done: agent.end_episode(); episode += 1
```

---

## Milestone 5 — Tests, Linting & Packaging

### Test Structure
```
tests/
├── conftest.py          # Shared fixtures (Grid, Agent, Env factories)
├── unit/
│   ├── test_grid.py     # in_bounds, is_walkable, CellType, load_from_dict
│   ├── test_wind.py     # prob=0 deterministic, prob=1 always deflects
│   ├── test_rewards.py  # all cell-type reward values
│   ├── test_env.py      # reset, step (wall/trap/goal/wind), termination
│   ├── test_q_table.py  # get/set, best_action, max_value, shape
│   ├── test_policy.py   # epsilon=0 exploits, epsilon=1 explores, decay
│   ├── test_agent.py    # Bellman update, done target, end_episode
│   └── test_sdk.py      # run_headless, save/load Q-table round-trip
└── integration/
    └── test_training_loop.py  # Full episode convergence smoke test
```

### Running Tests & Linting (via uv — mandatory)
```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
uv run ruff check src/
```

### Ruff Configuration (in pyproject.toml)
- Zero errors required — CI fails on any violation
- Rules: E, F, W, I, N, UP, B, C4, SIM
- Line length: 100

### Coverage Requirements
- Global: ≥ 85%
- GUI excluded from coverage (`omit = ["src/**/gui/*"]`)
- Branch + Statement coverage tracked

---

## Data Flow

```
setup.json + settings.yaml
         │
         ▼
    ConfigLoader ──► Logger
         │
         ├──► Grid ──► WindZone
         │        └──► RewardCalculator
         │                   │
         │                   ▼
         │             SmartCityEnv
         │                   │
         ├──► QTable          │ (state, reward, done)
         ├──► EpsilonGreedyPolicy   │
         │        └──► Agent ◄──────┘
         │                   │
         ▼                   ▼
    DroneRLSDK ──────────────────────► GUI Layer
                                   (Renderer, Heatmap,
                                    Arrows, Dashboard)
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `uv` only — no pip | Reproducible environments; locked deps via `uv.lock` |
| `Ruff` only — no flake8/pylint | Single fast linter; zero-error policy enforced in CI |
| `src/dronerl/` layout | Proper Python package; prevents import path bugs |
| `__init__.py` exports `__version__` | Version accessible at runtime: `import dronerl; dronerl.__version__` |
| `version.py` starts at `1.00` | All config files track matching version for compatibility checks |
| JSON for app config, YAML for RL params | JSON is version-controlled and machine-readable; YAML is human-friendly for tuning |
| SDK as single entry point | GUI and CLI have zero business logic; fully testable without Pygame |
| Separate `wind.py` | Wind logic independently testable and swappable |
| `RewardCalculator` class | Zero magic numbers; all rewards from config |
| Dashboard uses Pygame only | No Matplotlib overhead in real-time loop |
