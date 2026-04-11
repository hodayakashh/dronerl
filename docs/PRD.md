# Product Requirements Document — DroneRL

## Smart City Drone Delivery — Reinforcement Learning Simulation

---

## 1. Project Overview

### 1.1 Background

This project implements a tabular Q-Learning agent that learns to navigate a smart city
grid environment. The drone agent starts at a fixed position, avoids obstacles and traps,
handles stochastic wind zones, and must reach a goal cell in minimum steps. The environment
is a classic benchmark for tabular RL algorithms with added stochastic complexity.

### 1.2 User / Stakeholder

| Stakeholder | Goal |
|---|---|
| Student (developer) | Demonstrate understanding of Q-Learning and the Bellman equation |
| Course instructor (Dr. Segal) | Verify correct implementation of ε-greedy, Q-table update, convergence |
| Peer reviewers | Reproduce results using the provided config and README |

### 1.3 Problem Statement

Given a 12×12 grid representing a smart city with defined start, goal, trap, wind, and wall
cells, train a drone RL agent using Q-Learning so that it converges to the optimal
(shortest safe) path from start to goal.

---

## 2. Goals & Acceptance Criteria

### 2.1 Measurable Goals (KPIs)

| KPI | Target |
|---|---|
| Agent reaches goal | 100% of evaluation episodes (after training) |
| Convergence | Within 3000 episodes |
| Average reward (last 100 eps) | ≥ 80 |
| GUI frame rate | ≥ 60 FPS |
| Headless training speed | ≥ 5000 episodes/sec |
| Test coverage | ≥ 85% |
| Ruff lint errors | 0 |

### 2.2 Acceptance Criteria

- Agent finds optimal path in 12×12 grid within 3000 episodes.
- All unit tests pass with ≥ 85% coverage.
- Ruff linting: 0 errors.
- No hardcoded values in source code.

---

## 3. Functional Requirements

### 3.1 Environment Requirements

| ID | Requirement |
|---|---|
| FR-01 | 12×12 grid with configurable start, goal, wall, trap, and wind cells |
| FR-02 | Implement reset(), step(), and render() on the environment |
| FR-03 | Stochastic wind zones randomly deflect drone action with configurable probability |
| FR-04 | Episode terminates on: goal reached, trap hit, or max steps exceeded |
| FR-05 | Reward structure: step penalty, goal reward, trap penalty, wind penalty, wall penalty |

### 3.2 Agent Requirements

| ID | Requirement |
|---|---|
| FR-06 | Tabular Q-Learning with 3D Q-table shape (rows, cols, n_actions) |
| FR-07 | Epsilon-greedy action selection with configurable epsilon, decay, and min-epsilon |
| FR-08 | Bellman update after every step |
| FR-09 | Save/load Q-table to/from disk (numpy .npy format) |

### 3.3 GUI Requirements

| ID | Requirement |
|---|---|
| FR-10 | Real-time Pygame visualization at ≥ 60 FPS |
| FR-11 | Value heatmap overlay (toggleable, key H) |
| FR-12 | Policy arrows overlay (toggleable, key A) |
| FR-13 | Real-time reward and epsilon graphs (dashboard) |
| FR-14 | Interactive level editor (left-click cycles cell types, S saves, ESC exits) |

### 3.4 Success Metrics

* Agent converges to optimal policy within 3000 episodes
* Average reward over last 100 episodes reaches ≥ 80
* GUI runs at ≥ 60 FPS during training visualization
* Headless training achieves ≥ 5000 episodes/sec

* **KPIs:**
  * Episodes to convergence: ≤ 3000
  * Average reward (last 100 episodes): ≥ 80
  * GUI frame rate: ≥ 60 FPS
  * Headless training speed: ≥ 5000 episodes/sec

* **Acceptance Criteria:**
  * Agent finds optimal path in 12x12 grid within 3000 episodes
  * All unit tests pass with ≥ 85% coverage
  * Ruff linting: 0 errors
  * No hardcoded values in source code

### 3.5 User Stories

* As a student, I want to watch the drone learn in real-time so I can understand Q-Learning visually.
* As a student, I want to see the Q-value heatmap update so I can observe value propagation.
* As a researcher, I want to run headless training so I can benchmark hyperparameters quickly.
* As a user, I want to edit the level so I can create custom environments.
* As a user, I want to save/load Q-tables so I can resume training across sessions.

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | All config in config/ files — zero hardcoded values |
| NFR-02 | Files ≤ 150 lines; docstrings on every public function and class |
| NFR-03 | Test coverage ≥ 85% (pytest-cov) |
| NFR-04 | Ruff zero errors |
| NFR-05 | uv as sole package manager |
| NFR-06 | Reproducible results via fixed random seed in config |
| NFR-07 | Python 3.11+ required |

---

## 5. System Architecture

### Layers
1. **Configuration** — YAML/JSON config files loaded at startup
2. **Environment** — Grid, Wind, Rewards, SmartCityEnv
3. **Agent** — QTable, EpsilonGreedyPolicy, Agent
4. **SDK** — DroneRLSDK as single business-logic entry point
5. **GUI** — Renderer, Heatmap, Arrows, Dashboard, LevelEditor
6. **CLI** — main.py entry point

### Key Principle
All business logic routes through `DroneRLSDK`. GUI and CLI layers contain zero business logic.

---

## 6. Milestones & Timeline

| Milestone | Description |
|---|---|
| 1 | Project structure, config, documentation |
| 2 | Core RL engine: environment + agent |
| 3 | GUI, overlays, level editor |
| 4 | SDK integration, main loop, CLI |
| 5 | Tests, linting, packaging, delivery |

---

## 7. Dependencies & Out of Scope

### External Dependencies
* Python 3.11+, Pygame, NumPy, PyYAML, Matplotlib, Pytest, Ruff

### Out of Scope
* Deep RL (neural networks, function approximation)
* Multi-agent scenarios
* Real drone hardware integration
* Cloud deployment
