# Formation Boundary Feature with Automatic Reset

## Overview
This feature implements automatic position reset for robots that leave the defined formation area. When robots stray outside the boundary, the ARGoS loop function automatically moves them back to their original starting positions.

## Implementation Details

### Formation Boundaries
- **X-axis range**: 2.0 to 7.0 meters
- **Y-axis range**: 2.0 to 7.0 meters
- This creates a 5x5 meter square around the starting positions (3.5-4.5, 3.5-4.5)
- **Visual indication**: Formation area shown as green on the floor, goal area as cyan

### How It Works

1. **Original Position Storage**
   - Loop function stores each robot's initial position and orientation on startup
   - Controllers also store their original positions locally

2. **Formation Check (PreStep)**
   - Loop function checks every simulation step if robots are outside boundaries
   - If robot is outside: marks it for reset

3. **Automatic Reset (PostStep)**
   - Loop function uses `MoveEntity()` to physically reset robot positions
   - Robot is moved back to original coordinates with original orientation
   - Episode continues with robot at starting position

4. **Episode Management**
   - Controller detects boundary violation and ends episode
   - Controller sends RESET message to Python server (for logging)
   - Loop function automatically handles the physical reset

### Components

#### 1. ARGoS Loop Functions
**Files:**
- `loop_functions/q_swarm_loop_functions.h`
- `loop_functions/q_swarm_loop_functions.cpp`
- `loop_functions/CMakeLists.txt`

**Key Features:**
- Stores initial robot positions on Init()
- Monitors robot positions in PreStep()
- Resets robots using MoveEntity() in PostStep()
- Provides visual floor coloring (green = safe zone, cyan = goal)
#### 2. C++ Controller
**Files:**
- `controllers/q_swarm_controller/q_swarm_controller.h`
- `controllers/q_swarm_controller/q_swarm_controller.cpp`

**Key Features:**
- Stores formation boundaries and original position
- Checks if outside formation after 20 steps
- Ends episode when boundary violated (-10 reward)
- Sends RESET message to Python server for logging

## Running the System

**Use the test script:**
```bash
cd /home/shadow56/Desktop/minor-project
./test_formation_reset.sh
```

## What to Observe

When running, you should see:
1. `[LoopFunction] Initialized with 4 robots`
2. `[LoopFunction] Stored initial position for fb0: (3.5, 3.5)`
3. `[Robot fb3] LEFT FORMATION AREA! Position: (7.01, 4.71)`
4. `[LoopFunction] Robot fb3 left formation - will reset next step`
5. `[LoopFunction] ✓ Reset robot fb3 to (4.5, 4.5)`

The robots will automatically reset and continue training!

## Visual Feedback
- **Green floor** = Safe formation zone (2-7, 2-7)
- **Cyan floor** = Goal zone (17-19, 17-19) 
- **Gray floor** = Neutral area

## Summary
✅ **Automatic position reset implemented!**
✅ **No manual restart required**
✅ **Visual formation boundaries**
✅ **Seamless episode continuation**
