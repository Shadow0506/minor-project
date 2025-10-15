# Multi-Robot Reinforcement Learning Simulation in ARGoS

## 🎯 Project Overview

This project implements a Deep Q-Learning system where 4 FootBots learn to navigate to a goal while avoiding collisions in a 20×20m arena using ARGoS3 as the physics simulator.

## 🏗️ Architecture

```
Sensors → Q-Network → Action → ARGoS Environment → Reward → Q-Update
```

### Component Flow:
1. **ARGoS**: Simulates physics, robot movement, and collision detection
2. **C++ Controller**: Collects sensor data, communicates with Python Q-Network
3. **Python Q-Network**: Makes decisions, learns from rewards
4. **Communication**: Socket-based IPC between C++ and Python

## 📁 Project Structure

```
project_files/
├── README.md                      # This file
├── BUILD_INSTRUCTIONS.md          # Detailed build guide
├── controllers/
│   ├── q_swarm_controller/
│   │   ├── q_swarm_controller.h   # Controller header
│   │   ├── q_swarm_controller.cpp # Controller implementation
│   │   └── CMakeLists.txt         # Build configuration
├── experiments/
│   └── q_swarm_experiment.argos   # ARGoS configuration
├── python/
│   ├── q_network.py               # Deep Q-Learning network
│   ├── q_server.py                # Communication server
│   └── requirements.txt           # Python dependencies
└── models/
    └── (trained models saved here)
```

## ⚙️ System Parameters

| Parameter | Value |
|-----------|-------|
| Grid Size | 20 × 20 m |
| Number of Robots | 4 |
| Initial Spacing | 2 m |
| Velocity | 0.1 m/s |
| Max Episodes | 1000 |
| Goal Reward | +10 |
| Collision Penalty | -5 |
| Step Penalty | -0.1 |

## 🚀 Quick Start

### Prerequisites
- ARGoS3 installed
- CMake (3.10+)
- Python 3.8+
- PyTorch
- GCC/G++ compiler

### Installation Steps

1. **Install Python Dependencies**
```bash
cd python
pip install -r requirements.txt
```

2. **Build the C++ Controller**
```bash
cd controllers/q_swarm_controller
mkdir build
cd build
cmake ..
make
```

3. **Start the Q-Network Server**
```bash
cd python
python q_server.py
```

4. **Run ARGoS Simulation** (in another terminal)
```bash
argos3 -c experiments/q_swarm_experiment.argos
```

## 📊 What to Expect

- **Initial Behavior**: Robots move randomly, frequent collisions
- **After ~100 episodes**: Robots start avoiding walls and each other
- **After ~500 episodes**: Coordinated movement toward goal
- **After ~1000 episodes**: Efficient navigation with minimal collisions

## 🧠 Learning Process

1. Each robot observes its state (position + proximity sensors)
2. State is sent to Q-Network via socket
3. Q-Network predicts action (forward, left, right, stop)
4. Robot executes action in ARGoS
5. Reward is calculated based on outcome
6. Q-Network updates weights using experience replay
7. Process repeats for 1000 episodes

## 📈 Monitoring

- Watch the Qt-OpenGL visualization window
- Python console shows episode rewards
- Models are saved every 100 episodes

## 🔧 Troubleshooting

See `BUILD_INSTRUCTIONS.md` for detailed troubleshooting guide.

## 📝 License

Educational project for reinforcement learning demonstration.
