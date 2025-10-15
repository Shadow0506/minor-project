# 🛠️ Detailed Build and Run Instructions

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Building the Controller](#building-the-controller)
4. [Running the Simulation](#running-the-simulation)
5. [Communication Protocol](#communication-protocol)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. ARGoS3 Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install cmake libfreeimage-dev libfreeimageplus-dev \
  qt5-default freeglut3-dev libxi-dev libxmu-dev liblua5.3-dev \
  lua5.3 doxygen graphviz libgraphviz-dev asciidoc

git clone https://github.com/ilpincy/argos3.git
cd argos3
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ../src
make
sudo make install
```

**Windows:**
- Download ARGoS3 from: https://www.argos-sim.info/
- Follow Windows installation guide
- Add ARGoS to PATH

### 2. Python Setup

**Required Version:** Python 3.8 or higher

```bash
python --version  # Verify version
```

### 3. C++ Compiler

**Ubuntu:** `sudo apt-get install build-essential cmake`
**Windows:** Install Visual Studio with C++ tools or MinGW

---

## Environment Setup

### 1. Clone/Setup Project

```bash
cd "e:\College Work\Sem-5\Minor Project\project_files"
```

### 2. Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

This installs:
- torch (PyTorch for deep learning)
- numpy (numerical operations)
- matplotlib (plotting)

---

## Building the Controller

### Step 1: Navigate to Controller Directory

```bash
cd controllers/q_swarm_controller
```

### Step 2: Create Build Directory

```bash
mkdir build
cd build
```

### Step 3: Configure with CMake

```bash
cmake ..
```

**Expected Output:**
```
-- The C compiler identification is GNU X.X.X
-- The CXX compiler identification is GNU X.X.X
-- Configuring done
-- Generating done
-- Build files written to: .../build
```

### Step 4: Compile

```bash
make
```

**Expected Output:**
```
[ 50%] Building CXX object CMakeFiles/q_swarm_controller.dir/q_swarm_controller.cpp.o
[100%] Linking CXX shared library libq_swarm_controller.so
[100%] Built target q_swarm_controller
```

### Step 5: Verify Build

**Linux/Mac:**
```bash
ls -la libq_swarm_controller.so
```

**Windows:**
```bash
dir libq_swarm_controller.dll
```

---

## Running the Simulation

### Complete Workflow

#### Terminal 1: Start Q-Network Server

```bash
cd python
python q_server.py
```

**Expected Output:**
```
=== Q-Learning Server Started ===
Listening on localhost:5555
Waiting for ARGoS to connect...
```

**What it does:**
- Initializes the Q-Network
- Opens socket on port 5555
- Waits for controller connections

#### Terminal 2: Launch ARGoS

**Wait for "Waiting for ARGoS to connect..." message, then:**

```bash
cd experiments
argos3 -c q_swarm_experiment.argos
```

**Alternative (with GUI):**
```bash
argos3 -c q_swarm_experiment.argos
```

**Expected Output:**
```
[INFO] Loading library: libq_swarm_controller.so
[INFO] Controller 'q_swarm_controller' created
[INFO] Experiment initialized
[INFO] Starting simulation
```

### Simulation Controls

- **Play/Pause**: Space bar
- **Step**: Period (.)
- **Fast Forward**: Press play and increase speed slider
- **Reset**: Press reset button
- **Camera**: Click and drag to rotate, scroll to zoom

---

## Communication Protocol

### How C++ and Python Communicate

1. **Startup:**
   - Python server starts on port 5555
   - C++ controller connects as client
   - Handshake established

2. **Per Step:**
   ```
   C++ → Python: "STATE|robot_id|x|y|goal_x|goal_y|prox0|prox1|...|prox23"
   Python → C++: "ACTION|action_id"
   ```

3. **Episode End:**
   ```
   C++ → Python: "REWARD|robot_id|reward_value|done"
   Python → C++: "ACK"
   ```

### Message Format

**State Message:**
```
STATE|0|1.5|2.3|18.0|18.0|0.1|0.0|...|0.05
      │  │   │   │    │    └─── Proximity readings (24 values)
      │  │   │   └────┴──────── Goal position (x, y)
      │  └───┴──────────────── Robot position (x, y)
      └────────────────────── Robot ID
```

**Action Message:**
```
ACTION|2
       └── Action ID (0=forward, 1=left, 2=right, 3=stop)
```

---

## Troubleshooting

### Problem: "Cannot find libq_swarm_controller.so"

**Solution:**
```bash
export ARGOS_PLUGIN_PATH=$ARGOS_PLUGIN_PATH:/path/to/controllers/q_swarm_controller/build
```

Or add to `.argos` file:
```xml
<controllers>
  <q_swarm_controller id="qsc" library="/full/path/to/libq_swarm_controller.so">
```

### Problem: "Connection refused" on Python server

**Check:**
1. Is `q_server.py` running?
2. Is port 5555 available? `netstat -an | grep 5555`
3. Firewall blocking connection?

**Solution:**
```bash
# Kill process on port 5555
lsof -ti:5555 | xargs kill -9

# Restart server
python q_server.py
```

### Problem: Robots not moving

**Check:**
1. Controller loaded? Look for "Controller 'q_swarm_controller' created" in ARGoS output
2. Actions being received? Add debug prints in controller
3. Wheel velocities set? Check `SetLinearVelocity()` calls

### Problem: "CMake Error: Could not find ARGoS"

**Solution:**
```bash
# Find ARGoS installation
find /usr -name "argos3"

# Set ARGoS path
export ARGOS3_DIR=/usr/local

# Or specify in cmake
cmake -DARGOS3_DIR=/usr/local ..
```

### Problem: PyTorch not found

**Solution:**
```bash
# CPU version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# GPU version (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## Performance Tips

1. **Speed up training:**
   - Disable visualization: `argos3 -c experiment.argos -n` (no GUI)
   - Reduce physics updates in .argos file
   - Use GPU for Q-Network (modify `q_network.py`)

2. **Monitor training:**
   - Check `python/training_log.txt`
   - Plot rewards: Run after training completes
   - Visualize policies: See robot behaviors

3. **Improve learning:**
   - Adjust learning rate in `q_network.py`
   - Modify reward structure in controller
   - Increase replay buffer size

---

## Expected Training Timeline

| Episodes | Expected Behavior |
|----------|-------------------|
| 0-100 | Random exploration, many collisions |
| 100-300 | Basic obstacle avoidance |
| 300-600 | Goal-directed movement |
| 600-900 | Multi-robot coordination |
| 900-1000 | Optimized navigation |

---

## Verification Checklist

- [ ] ARGoS3 installed and `argos3 --version` works
- [ ] Python 3.8+ with PyTorch installed
- [ ] Controller compiled successfully (`.so` or `.dll` file exists)
- [ ] Q-Network server starts without errors
- [ ] ARGoS connects to Python server
- [ ] Robots visible in visualization
- [ ] Console shows episode rewards
- [ ] Models saved in `models/` directory

---

## Next Steps

After successful run:
1. Analyze training curves
2. Test trained model (load saved weights)
3. Modify reward function for different behaviors
4. Add more robots or obstacles
5. Implement different RL algorithms (A3C, PPO)

---

## Support

For issues:
1. Check ARGoS documentation: https://www.argos-sim.info/
2. Review error messages in both terminals
3. Enable debug mode in controller (set `DEBUG = true`)
