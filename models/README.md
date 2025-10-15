# Models Directory

This directory will contain trained Q-Network models and training data.

## Files Created During Training

- `q_network_latest.pth` - Most recent model (updated continuously)
- `q_network_episode_25.pth` - Checkpoint at episode 25
- `q_network_episode_50.pth` - Checkpoint at episode 50
- `q_network_episode_75.pth` - Checkpoint at episode 75
- ... (every 25 episodes)
- `q_network_final.pth` - Final trained model
- `training_data.json` - Episode rewards and statistics
- `training_curve.png` - Visualization of training progress

## Loading a Trained Model

```python
from q_network import QNetworkAgent

agent = QNetworkAgent()
agent.load_model("models/q_network_final.pth")
agent.epsilon = 0.0  # Pure exploitation, no exploration
```

## Model Contents

Each `.pth` file contains:
- Q-Network state dict (weights and biases)
- Target Network state dict
- Optimizer state dict
- Current epsilon value
- Episode rewards history

## File Size

Each model checkpoint is approximately 200-500 KB.
