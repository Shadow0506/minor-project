# 🧠 Architecture Explanation: Multi-Robot Reinforcement Learning with ARGoS

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Communication Flow](#communication-flow)
4. [Deep Q-Learning Explained](#deep-q-learning-explained)
5. [ARGoS Integration](#argos-integration)
6. [Learning Process](#learning-process)
7. [Code Walkthrough](#code-walkthrough)

---

## System Overview

This project demonstrates **multi-robot reinforcement learning** where 4 FootBots learn to navigate to a goal while avoiding collisions using **Deep Q-Learning (DQN)**.

### Key Components:

```
┌─────────────────────────────────────────────────────────────┐
│                     ARGoS Simulator                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  FootBot 0 │  │  FootBot 1 │  │  FootBot 2 │  ...      │
│  │ Controller │  │ Controller │  │ Controller │           │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘           │
│         │ Sensors        │                │                 │
│         │ Actuators      │                │                 │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          │    Socket Communication (TCP)   │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Q-Network Server                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Deep Q-Network (PyTorch)                 │  │
│  │  - State Input Layer (28 neurons)                    │  │
│  │  - Hidden Layers (128-128-128)                       │  │
│  │  - Action Output Layer (4 neurons)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Experience Replay Buffer                 │  │
│  │  Stores: (state, action, reward, next_state, done)   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. ARGoS Simulator (Physics Engine)

**Purpose**: Provides realistic robot physics and environment simulation

**Key Features**:
- **20×20m arena** with walls
- **FootBot robots** with differential drive
- **Proximity sensors** (24 sensors around robot)
- **Positioning sensor** (GPS-like localization)
- **Collision detection**
- **Real-time visualization**

**Configuration**: `experiments/q_swarm_experiment.argos`

### 2. C++ Robot Controller

**Purpose**: Interfaces between ARGoS and Python Q-Network

**File**: `controllers/q_swarm_controller/q_swarm_controller.cpp`

**Responsibilities**:
1. **Sense**: Collect data from sensors
2. **Communicate**: Send state to Q-Network via socket
3. **Act**: Receive action and control wheels
4. **Evaluate**: Calculate rewards
5. **Feedback**: Send rewards back to Q-Network

**Key Methods**:
- `GetState()`: Collects sensor readings
- `GetActionFromQNetwork()`: Requests action
- `ExecuteAction()`: Controls robot motors
- `CalculateReward()`: Computes reward
- `SendReward()`: Provides feedback for learning

### 3. Python Q-Network

**Purpose**: Makes decisions and learns from experience

**File**: `python/q_network.py`

**Architecture**:
```python
Input Layer (28 neurons)
    ↓
Hidden Layer 1 (128 neurons, ReLU)
    ↓
Hidden Layer 2 (128 neurons, ReLU)
    ↓
Hidden Layer 3 (128 neurons, ReLU)
    ↓
Output Layer (4 neurons) → Q-values for each action
```

**Actions**:
- `0`: Move Forward
- `1`: Turn Left
- `2`: Turn Right
- `3`: Stop

### 4. Communication Server

**Purpose**: Manages socket communication between C++ and Python

**File**: `python/q_server.py`

**Protocol**:
```
C++ → Python: "STATE|robot_id|x|y|goal_x|goal_y|prox0|prox1|...|prox23"
Python → C++: "ACTION|action_id"

C++ → Python: "REWARD|robot_id|reward_value|done"
Python → C++: "ACK"
```

---

## Communication Flow

### Single Step Cycle:

```
1. Robot Controller (C++)
   ├─ Read sensors (position + proximity)
   ├─ Build state vector [28 values]
   └─ Send to Python via socket
          ↓
2. Q-Network Server (Python)
   ├─ Receive state
   ├─ Forward through neural network
   ├─ Select action (ε-greedy)
   └─ Send action back
          ↓
3. Robot Controller (C++)
   ├─ Receive action
   ├─ Execute action (set wheel speeds)
   ├─ ARGoS updates physics
   ├─ Calculate reward
   └─ Send reward to Python
          ↓
4. Q-Network Server (Python)
   ├─ Store (s, a, r, s', done) in replay buffer
   ├─ Sample batch from buffer
   ├─ Compute Q-learning update
   ├─ Backpropagate and update weights
   └─ Ready for next step
```

### Episode Cycle:

```
Episode Start
    ↓
[Repeat for max_steps or until done]
    ├─ Get state
    ├─ Select action
    ├─ Execute action
    ├─ Calculate reward
    └─ Update Q-Network
    ↓
Episode End
    ├─ Log episode reward
    ├─ Reset robot position
    ├─ Decay epsilon
    └─ Save model (every 25 episodes)
```

---

## Deep Q-Learning Explained

### What is Q-Learning?

Q-Learning learns a **Q-function** Q(s, a) that predicts the expected future reward for taking action `a` in state `s`.

**Goal**: Find optimal policy π*(s) = argmax_a Q(s, a)

### Deep Q-Network (DQN)

Instead of storing Q-values in a table, we use a **neural network** to approximate Q(s, a).

### Key Algorithms:

#### 1. Epsilon-Greedy Exploration

```python
if random() < epsilon:
    action = random_action()  # Explore
else:
    action = argmax(Q(state))  # Exploit
```

- **High epsilon (1.0)**: Random exploration (early training)
- **Low epsilon (0.01)**: Greedy exploitation (late training)

#### 2. Experience Replay

Store experiences `(s, a, r, s', done)` in a buffer and sample randomly for training.

**Benefits**:
- Breaks correlation between consecutive samples
- Reuses experiences multiple times
- Improves sample efficiency

#### 3. Target Network

Maintain two networks:
- **Q-Network**: Updated every step
- **Target Network**: Updated periodically (every 100 steps)

**Loss Function**:
```
L = (Q(s, a) - target)²

where target = r + γ × max_a' Q_target(s', a')
```

**Benefits**:
- Stabilizes training
- Prevents divergence

### Training Update:

```python
1. Sample batch from replay buffer
2. Compute current Q-values: Q(s, a)
3. Compute target Q-values: r + γ × max_a' Q_target(s', a')
4. Compute loss: MSE(Q_current, Q_target)
5. Backpropagate and update Q-Network weights
6. Every 100 steps: Q_target ← Q
7. Decay epsilon
```

---

## ARGoS Integration

### Why ARGoS?

1. **Physics Realism**: Accurate robot dynamics
2. **Scalability**: Handles multiple robots efficiently
3. **Visualization**: Real-time 3D rendering
4. **Extensibility**: C++ plugin system
5. **Community**: Well-documented, widely used

### FootBot Robot

**Sensors**:
- **Proximity Sensors**: 24 infrared sensors (0-1 range)
  - Detect obstacles, walls, other robots
  - 360° coverage
- **Positioning Sensor**: (x, y, θ)
  - Absolute position in arena
  - Orientation

**Actuators**:
- **Differential Steering**: Left/right wheel speeds
  - Forward: both wheels same speed
  - Turn: differential speeds

### Arena Setup

```xml
<arena size="20, 20, 2">
  <!-- Walls -->
  <box id="wall_north" size="20, 0.1, 0.5" position="10, 20, 0" />
  <box id="wall_south" size="20, 0.1, 0.5" position="10, 0, 0" />
  <box id="wall_east" size="0.1, 20, 0.5" position="20, 10, 0" />
  <box id="wall_west" size="0.1, 20, 0.5" position="0, 10, 0" />
  
  <!-- Goal marker -->
  <box id="goal" size="1, 1, 0.1" position="18, 18, 0" />
  
  <!-- Robots -->
  <foot-bot id="fb0" position="2, 2, 0" />
  <foot-bot id="fb1" position="2, 4, 0" />
  <foot-bot id="fb2" position="4, 2, 0" />
  <foot-bot id="fb3" position="4, 4, 0" />
</arena>
```

---

## Learning Process

### State Representation (28 dimensions)

```python
state = [
    x,              # Robot X position (0-20)
    y,              # Robot Y position (0-20)
    goal_x,         # Goal X position (18.0)
    goal_y,         # Goal Y position (18.0)
    prox_0,         # Proximity sensor 0 (0-1)
    prox_1,         # Proximity sensor 1 (0-1)
    ...
    prox_23         # Proximity sensor 23 (0-1)
]
```

### Action Space (4 discrete actions)

```
0: Move Forward   → Left wheel: +v, Right wheel: +v
1: Turn Left      → Left wheel: -v/2, Right wheel: +v/2
2: Turn Right     → Left wheel: +v/2, Right wheel: -v/2
3: Stop           → Left wheel: 0, Right wheel: 0
```

### Reward Function

```python
reward = -0.1  # Small step penalty (encourages efficiency)

if reached_goal:
    reward = +10.0  # Big positive reward
    done = True

elif collision_detected:
    reward = -5.0   # Negative penalty
    done = True

return reward, done
```

**Design Rationale**:
- **Step penalty (-0.1)**: Encourages faster solutions
- **Goal reward (+10)**: Primary objective
- **Collision penalty (-5)**: Avoids destructive behavior

### Training Phases

#### Phase 1: Random Exploration (Episodes 0-100)
- **Epsilon**: 1.0 → 0.6
- **Behavior**: Mostly random actions
- **Learning**: Building initial replay buffer
- **Rewards**: Highly negative (many collisions)

#### Phase 2: Basic Navigation (Episodes 100-300)
- **Epsilon**: 0.6 → 0.3
- **Behavior**: Learns to avoid walls
- **Learning**: Q-values start to converge
- **Rewards**: Less negative, occasional goals

#### Phase 3: Goal-Directed (Episodes 300-600)
- **Epsilon**: 0.3 → 0.1
- **Behavior**: Moves toward goal
- **Learning**: Refining optimal paths
- **Rewards**: Increasingly positive

#### Phase 4: Coordination (Episodes 600-900)
- **Epsilon**: 0.1 → 0.02
- **Behavior**: Multi-robot coordination
- **Learning**: Fine-tuning policies
- **Rewards**: Consistently positive

#### Phase 5: Optimization (Episodes 900-1000)
- **Epsilon**: 0.02 → 0.01
- **Behavior**: Near-optimal navigation
- **Learning**: Exploitation mode
- **Rewards**: Maximum efficiency

---

## Code Walkthrough

### C++ Controller - Main Loop

```cpp
void QSwarmController::ControlStep() {
    // 1. Collect sensor data
    std::vector<float> state = GetState();
    
    // 2. Get action from Q-Network
    int action = GetActionFromQNetwork(state);
    
    // 3. Execute action
    ExecuteAction(action);
    
    // 4. Calculate reward
    bool done = false;
    float reward = CalculateReward(done);
    
    // 5. Send feedback
    SendReward(reward, done);
    
    // 6. Check episode termination
    if (done || steps >= max_steps) {
        ResetEpisode();
    }
}
```

### Python Q-Network - Action Selection

```python
def select_action(self, state, robot_id):
    # Epsilon-greedy policy
    if np.random.rand() < self.epsilon:
        # Explore: random action
        action = np.random.randint(0, 4)
    else:
        # Exploit: best action from Q-network
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        action = q_values.argmax().item()
    
    return action
```

### Python Q-Network - Training Update

```python
def train(self):
    # Sample batch from replay buffer
    batch = self.replay_buffer.sample(batch_size)
    states, actions, rewards, next_states, dones = zip(*batch)
    
    # Convert to tensors
    states = torch.FloatTensor(states)
    actions = torch.LongTensor(actions)
    rewards = torch.FloatTensor(rewards)
    next_states = torch.FloatTensor(next_states)
    dones = torch.FloatTensor(dones)
    
    # Current Q-values
    current_q = self.q_network(states).gather(1, actions.unsqueeze(1))
    
    # Target Q-values
    with torch.no_grad():
        next_q = self.target_network(next_states).max(1)[0]
        target_q = rewards + (1 - dones) * gamma * next_q
    
    # Compute loss and update
    loss = MSELoss(current_q.squeeze(), target_q)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Update target network periodically
    if step % target_update_freq == 0:
        self.target_network.load_state_dict(self.q_network.state_dict())
```

---

## Key Insights

### Why This Demonstrates Reinforcement Learning

1. **Agent-Environment Interaction**
   - Robots (agents) interact with ARGoS (environment)
   - Continuous feedback loop

2. **Reward-Driven Learning**
   - No explicit programming of navigation logic
   - Learns purely from rewards

3. **Exploration vs. Exploitation**
   - Epsilon-greedy balances trying new actions vs. using learned knowledge

4. **Temporal Credit Assignment**
   - Learns which actions lead to long-term success
   - Delayed rewards (goal reached many steps later)

5. **Multi-Agent Learning**
   - Multiple robots learn simultaneously
   - Implicitly learns coordination (avoiding each other)

### Challenges Addressed

1. **High-Dimensional State Space**
   - Neural network approximates Q-function

2. **Continuous Environment**
   - Discretized actions, continuous state

3. **Sample Efficiency**
   - Experience replay reuses data

4. **Stability**
   - Target network prevents oscillation

5. **Scalability**
   - Each robot has independent Q-network instance
   - Can scale to more robots

---

## Extending the System

### Ideas for Enhancement:

1. **Dynamic Obstacles**: Add moving obstacles
2. **Multi-Goal**: Different goals for each robot
3. **Communication**: Explicit robot-to-robot messages
4. **Different Algorithms**: PPO, A3C, MADDPG
5. **Transfer Learning**: Pre-train, then fine-tune
6. **Curriculum Learning**: Gradually increase difficulty

---

## Conclusion

This project demonstrates a complete reinforcement learning system integrating:
- **ARGoS**: Realistic physics simulation
- **Deep Q-Learning**: Neural network-based decision making
- **Multi-Robot**: Simultaneous learning and coordination
- **Socket Communication**: C++/Python interoperability

The robots learn complex navigation behaviors purely from reward feedback, showcasing the power of reinforcement learning in robotics.

---

**Happy Learning! 🤖🧠**
