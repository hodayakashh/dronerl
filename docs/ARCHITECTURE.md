# DroneRL — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Entry Points                          │
│    CLI (main.py)              GUI (_gui_runner.py)           │
│         │                           │                        │
│         └──────────┬────────────────┘                        │
│                    ▼                                         │
│              DroneRLSDK  (sdk.py)                            │
│          ┌──────────────────────┐                            │
│          │  Single facade for   │                            │
│          │  all business logic  │                            │
│          └──────────────────────┘                            │
│               │            │                                 │
│       ┌───────┘            └───────┐                         │
│       ▼                            ▼                         │
│  Environment Layer           Agent Layer                     │
│  ┌─────────────────┐   ┌──────────────────────┐             │
│  │  SmartCityEnv   │   │       Agent           │             │
│  │  ┌───────────┐  │   │  ┌───────────────┐   │             │
│  │  │   Grid    │  │   │  │    QTable     │   │             │
│  │  ├───────────┤  │   │  ├───────────────┤   │             │
│  │  │ WindZone  │  │   │  │EpsilonGreedy  │   │             │
│  │  ├───────────┤  │   │  │   Policy      │   │             │
│  │  │  Reward   │  │   │  └───────────────┘   │             │
│  │  │Calculator │  │   └──────────────────────┘             │
│  │  └───────────┘  │                                         │
│  └─────────────────┘                                         │
│                                                              │
│  GUI Layer (omitted from coverage)                           │
│  ┌──────────┬──────────┬───────────┬──────────────────────┐ │
│  │Renderer  │ Heatmap  │  Arrows   │     Dashboard        │ │
│  │          │ Overlay  │  Overlay  │  (stats + legend)    │ │
│  └──────────┴──────────┴───────────┴──────────────────────┘ │
│                                                              │
│  Shared Layer                                                │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │ ConfigLoader │  get_logger  │       version.py         │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow — Training Step

```
Agent.select_action(state)
        │  ε-greedy: explore or exploit Q-table
        ▼
actual_action = WindZone.apply(action)   ← only if current cell is WIND
        │
        ▼
SmartCityEnv.step(actual_action)
        │  compute next_state, reward, done
        ▼
Agent.update(state, action, reward, next_state, done)
        │  Bellman: Q[s,a] += α*(r + γ*max Q[s'] - Q[s,a])
        ▼
   state = next_state
```

## Q-Learning Update Rule

```
target = r                          if terminal
target = r + γ · max Q(s', a')     otherwise

Q(s, a) ← Q(s, a) + α · (target − Q(s, a))
```

**Hyperparameters (config/settings.yaml):**

| Parameter | Value | Description |
|-----------|-------|-------------|
| α (alpha) | 0.1 | Learning rate |
| γ (gamma) | 0.95 | Discount factor |
| ε start | 1.0 | Initial exploration rate |
| ε min | 0.01 | Minimum exploration rate |
| ε decay | 0.995 | Multiplicative decay per episode |
| max_steps | 200 | Steps per episode cap |

## Module Dependency Graph

```
main.py ──► sdk.py ──► environment/ ──► grid.py
                  │                └──► wind.py
                  │                └──► rewards.py
                  │                └──► env.py
                  │
                  └──► agent/ ──► q_table.py
                  │          └──► policy.py
                  │          └──► agent.py
                  │
                  └──► shared/ ──► config.py
                  │           └──► logger.py
                  │           └──► version.py
                  │
_gui_runner.py ──► gui/ ──► renderer.py
                       └──► heatmap.py
                       └──► arrows.py
                       └──► dashboard.py
                       └──► level_editor.py
```

## Key Design Principles

1. **SDK Facade** — All business logic behind `DroneRLSDK`. GUI/CLI have zero RL logic.
2. **Dependency Injection** — All components receive dependencies via constructor.
3. **Config-Driven** — No hardcoded values; all parameters in `config/`.
4. **Coverage Boundary** — `main.py`, `_gui_runner.py`, and `gui/` excluded from coverage
   (Pygame rendering is not unit-testable); core logic achieves 97% coverage.
5. **File Size Cap** — All files ≤ 150 lines enforces single responsibility.
