# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, verify you have:

- [ ] ARGoS3 installed (`argos3 --version`)
- [ ] Python 3.8+ (`python --version`)
- [ ] CMake 3.10+ (`cmake --version`)
- [ ] C++ compiler (gcc/g++ or MSVC)

## Windows-Specific Setup

### 1. Install Python Dependencies

```cmd
cd python
pip install -r requirements.txt
```

### 2. Build C++ Controller

```cmd
cd controllers\q_swarm_controller
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

### 3. Set Environment Variable (if needed)

If ARGoS can't find the controller library:

```cmd
set ARGOS_PLUGIN_PATH=%CD%\controllers\q_swarm_controller\build
```

Or add the full path to the `.argos` file.

## Running the Simulation

### Terminal 1: Start Python Server

```cmd
cd python
python q_server.py
```

Wait for: `Waiting for ARGoS to connect...`

### Terminal 2: Launch ARGoS

```cmd
cd experiments
argos3 -c q_swarm_experiment.argos
```

## What You'll See

### Python Terminal Output:
```
=== Q-Learning Server Started ===
Listening on localhost:5555
Waiting for ARGoS to connect...

[INFO] Connection from ('127.0.0.1', 54321)
[TRAIN] Step 100 | Loss: 0.0234 | Epsilon: 0.9850 | Buffer: 100
[EPISODE] Robot 0 | Steps: 125 | Reward: -12.50
[EPISODE] Robot 1 | Steps: 98 | Reward: -9.80
...
```

### ARGoS Window:
- 4 FootBots moving in 20×20m arena
- Green goal marker at (18, 18)
- Initially random movement
- Gradually more coordinated behavior

## Controls

**In ARGoS GUI:**
- **Space**: Play/Pause
- **Period (.)**: Step forward
- **R**: Reset
- **Mouse**: Rotate camera (drag)
- **Scroll**: Zoom

## Training Progress

| Episode Range | Expected Behavior |
|---------------|-------------------|
| 1-100 | Random exploration, collisions |
| 100-300 | Wall avoidance learned |
| 300-600 | Goal-directed movement |
| 600-900 | Multi-robot coordination |
| 900-1000 | Optimized paths |

## Monitoring

### View Training Curve (after training):

```cmd
cd python
python visualize.py plot
```

### View Statistics:

```cmd
python visualize.py stats
```

## Common Issues

### Issue: "Cannot find libq_swarm_controller"

**Fix:** Edit `experiments/q_swarm_experiment.argos` and change:

```xml
library="controllers/q_swarm_controller/build/libq_swarm_controller"
```

to the full absolute path:

```xml
library="E:\College Work\Sem-5\Minor Project\project_files\controllers\q_swarm_controller\build\q_swarm_controller.dll"
```

### Issue: "Connection refused"

**Fix:** Ensure Python server is running BEFORE starting ARGoS.

### Issue: Robots not moving

**Fix:** Check that actions are being sent. Add debug in controller.

## Next Steps

1. Let it train for 1000 episodes
2. View training curve: `python visualize.py plot`
3. Test trained model with epsilon=0
4. Experiment with different rewards
5. Add more robots or obstacles

## File Locations

- **Models saved**: `models/q_network_episode_XXX.pth`
- **Training data**: `models/training_data.json`
- **Plots**: `models/training_curve.png`

## Stopping

1. Close ARGoS window
2. Press `Ctrl+C` in Python terminal
3. Models are automatically saved

---

**Enjoy your reinforcement learning simulation! 🤖**
