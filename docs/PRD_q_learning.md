# PRD — Q-Learning Algorithm (Tabular)

## DroneRL — Algorithm-Specific Requirements

---

## 1. Background & Theory

Tabular Q-Learning is a model-free reinforcement learning algorithm that learns
the optimal action-value function Q*(s, a) through direct interaction with the
environment. It is based on the Bellman optimality equation:

```
Q(s, a) ← Q(s, a) + α · [r + γ · max_a' Q(s', a') − Q(s, a)]
```

Where:
- `Q(s, a)` — expected cumulative reward for taking action `a` in state `s`
- `α` — learning rate (how fast to update)
- `γ` — discount factor (how much future rewards are valued)
- `r` — immediate reward received
- `s'` — next state
- `max_a' Q(s', a')` — best expected future value

The algorithm is **off-policy** (learns optimal policy regardless of behavior policy)
and **model-free** (does not require knowledge of transition probabilities P(s'|s,a)).

---

## 2. Specific Requirements

### 2.1 Q-Table
- 3D NumPy array of shape `(rows, cols, n_actions)`, dtype `float32`
- Initialized to zeros
- Must support save/load (numpy `.npy` format)

### 2.2 Bellman Update
- Applied after every step: `Q[s,a] += alpha * (target - Q[s,a])`
- Terminal step target: `target = reward` (no future value)
- Non-terminal target: `target = reward + gamma * max(Q[s'])`

### 2.3 Epsilon-Greedy Exploration
- `epsilon_start = 1.0` (full exploration at start)
- `epsilon_min = 0.01` (minimum 1% exploration forever)
- Decay: `epsilon = max(epsilon * decay, epsilon_min)` after each episode
- Action selection:
  - With prob `epsilon`: random action (uniform over 4 directions)
  - With prob `1 - epsilon`: `argmax(Q[s])`

### 2.4 Convergence Criteria
- Agent must find the optimal path in a 12×12 grid within 3000 episodes
- Optimal path measured as: average reward over last 100 episodes ≥ 80

---

## 3. Input / Output / Setup

### Input (per step)
- Current state: `(row, col)` tuple
- Reward: float (from RewardCalculator)
- Next state: `(row, col)` tuple
- Done: bool

### Output (per step)
- Updated Q-value at `Q[row, col, action]`

### Setup Parameters (from config/settings.yaml)
| Parameter | Type | Default | Range |
|---|---|---|---|
| alpha | float | 0.1 | (0, 1] |
| gamma | float | 0.95 | (0, 1) |
| epsilon_start | float | 1.0 | [0, 1] |
| epsilon_min | float | 0.01 | [0, 1] |
| epsilon_decay | float | 0.995 | (0, 1) |
| max_episodes | int | 3000 | > 0 |
| max_steps | int | 200 | > 0 |

---

## 4. Constraints & Trade-offs

| Constraint | Reason |
|---|---|
| Tabular (not DNN) | Educational clarity; state space fits in memory |
| 4 discrete actions only | Simplicity; no diagonal movement |
| Fully observable state | No partial observability needed for this scope |
| CPU only | No GPU required for tabular RL on 12×12 grid |

### Alternatives Considered
- **SARSA (on-policy)**: Would converge more conservatively; Q-Learning chosen for demonstrating optimal policy learning
- **Double Q-Learning**: Reduces overestimation bias; excluded to keep implementation simple for educational purposes
- **Function approximation (DQN)**: Out of scope per PRD section 7

---

## 5. Success Criteria & Test Scenarios

### Success Criteria
- Convergence within 3000 episodes on default 12×12 map
- Average reward (last 100 eps) ≥ 80
- Q-table correctly reflects: high values near goal, low near traps

### Specific Test Scenarios
| Scenario | Expected Behavior |
|---|---|
| `epsilon=0`, optimal Q-table | Always takes best action (no exploration) |
| `epsilon=1` | Always random action |
| `alpha=0` | Q-values never change (no learning) |
| `gamma=0` | Only immediate rewards matter; no planning |
| Terminal step update | `target = reward` (no `max Q[s']` term) |
| Wind deflects action | Agent still updates Q correctly for actual transition |
| Wall collision | Agent stays in place; wall penalty applied |
| Trap reached | Episode ends immediately; trap penalty applied |
| Goal reached | Episode ends; goal reward applied |
