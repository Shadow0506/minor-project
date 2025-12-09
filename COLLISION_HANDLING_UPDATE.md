# Collision Handling Update

## Date: 10 December 2025

## Previous Behavior (Option 1 - End on Collision)
The robots were using a **hard reset** approach:
- Any collision immediately ended the episode
- Robots would reset to starting positions
- This caused robots to get stuck in loops: move → collide → reset → repeat
- Poor learning because episodes were too short (typically 4 steps)

**Evidence from logs:**
```
[t=276] [Robot fb1] COLLISION DETECTED!
[t=276] [Robot fb1] Episode 1 ended. Steps: 4, Reward: -8.08275
[t=277] [Robot fb1] Starting episode 2
```

## New Behavior (Option 2 - Continue After Collision)
Now implementing the **recommended soft constraint** approach:

### Key Changes:

1. **Collisions don't immediately end episodes**
   - Robot receives -10.0 reward penalty
   - Episode continues
   - Robot can learn recovery behaviors

2. **Collision counter with threshold**
   - Tracks collisions per episode
   - Maximum of 5 collisions allowed per episode
   - After 5 collisions → hard episode termination
   - This prevents robots from "accepting" constant collisions

3. **Better learning dynamics**
   - Robots can learn long-horizon behaviors
   - Can learn collision avoidance AND recovery
   - Credit assignment is clearer (specific collision → specific penalty)
   - Episodes can be longer and more informative

### Code Changes:

**File: `q_swarm_controller.h`**
- Added `m_nCollisionCount` - tracks collisions in current episode
- Added `m_nMaxCollisionsPerEpisode` - threshold (default: 5)

**File: `q_swarm_controller.cpp`**

1. **Constructor** - Initialize collision tracking:
```cpp
m_nCollisionCount(0),
m_nMaxCollisionsPerEpisode(5)
```

2. **CalculateReward()** - Collision handling logic:
```cpp
if (m_nSteps > 3 && DetectCollision()) {
    m_nCollisionCount++;
    reward = -10.0f;
    
    // Only end if too many collisions
    if (m_nCollisionCount >= m_nMaxCollisionsPerEpisode) {
        done = true;
        // Log and return
    }
    
    // Otherwise continue episode with penalty
}
```

3. **ResetEpisode()** - Reset counter:
```cpp
m_nCollisionCount = 0;
```

## Benefits:

✅ **Longer episodes** - Robots can learn complex navigation patterns  
✅ **Recovery learning** - Robots learn what to do after a collision  
✅ **Better exploration** - More samples from each episode  
✅ **Realistic behavior** - Models real-world scenarios where minor bumps happen  
✅ **Balanced constraints** - Soft penalty that becomes hard if abused  

## Expected Outcomes:

- Episodes will be longer (dozens to hundreds of steps vs. 4 steps)
- Robots will learn to:
  - Avoid collisions when possible
  - Recover gracefully when collisions occur
  - Navigate around obstacles while maintaining swarm formation
- Better swarm coordination without premature episode termination

## Testing:

Rebuild and run to see the new behavior:
```bash
cd controllers/q_swarm_controller/build
make
cd ../../..
./run_server.bat  # In one terminal (Python)
./run_argos.bat   # In another terminal (ARGoS)
```

Look for logs like:
```
[Robot fb1] COLLISION DETECTED! Count: 1/5 (continuing episode)
```

Instead of immediate episode endings.
