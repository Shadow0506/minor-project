"""
Dueling Double Deep Q-Network (D3Q) Implementation

This module implements a Dueling Double Deep Q-Learning network using PyTorch.
It includes:
- Dueling architecture (Value and Advantage streams)
- Double Q-Network for reduced overestimation
- Experience replay buffer with prioritization
- Training logic with gradient clipping
- Model saving/loading
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
import os


class D3QNetwork(nn.Module):
    """
    Dueling Double Deep Q-Network architecture
    
    Features:
    - Dueling architecture: Separate value and advantage streams
    - This allows the network to learn state values independently of specific actions
    
    Input: State vector [x, y, goal_x, goal_y, prox_0, ..., prox_23]
           Total size: 4 + 24 = 28
    Output: Q-values for 4 actions [forward, left, right, stop]
    """
    
    def __init__(self, state_size=28, action_size=4, hidden_size=128):
        super(D3QNetwork, self).__init__()
        
        # Shared feature extraction layers
        self.feature_layer1 = nn.Linear(state_size, hidden_size)
        self.feature_layer2 = nn.Linear(hidden_size, hidden_size)
        self.relu = nn.ReLU()
        
        # Value stream (estimates V(s))
        self.value_layer1 = nn.Linear(hidden_size, hidden_size // 2)
        self.value_layer2 = nn.Linear(hidden_size // 2, 1)
        
        # Advantage stream (estimates A(s,a))
        self.advantage_layer1 = nn.Linear(hidden_size, hidden_size // 2)
        self.advantage_layer2 = nn.Linear(hidden_size // 2, action_size)
        
        self.action_size = action_size
        
    def forward(self, x):
        """
        Forward pass with dueling architecture
        Q(s,a) = V(s) + (A(s,a) - mean(A(s,a')))
        """
        # Feature extraction
        x = self.relu(self.feature_layer1(x))
        x = self.relu(self.feature_layer2(x))
        
        # Value stream
        value = self.relu(self.value_layer1(x))
        value = self.value_layer2(value)
        
        # Advantage stream
        advantage = self.relu(self.advantage_layer1(x))
        advantage = self.advantage_layer2(advantage)
        
        # Combine value and advantage (with mean normalization)
        # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a')))
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        
        return q_values


class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay Buffer
    
    Stores transitions with priority based on TD-error
    - Higher TD-error experiences are sampled more frequently
    - Helps the network learn from important transitions faster
    """
    
    def __init__(self, capacity=10000, alpha=0.6, beta=0.4):
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
        self.alpha = alpha  # How much prioritization to use (0 = no priority, 1 = full)
        self.beta = beta    # Importance sampling correction
        self.epsilon = 1e-6  # Small constant to ensure non-zero priorities
        
    def push(self, state, action, reward, next_state, done, td_error=1.0):
        """Add transition with priority"""
        self.buffer.append((state, action, reward, next_state, done))
        # Priority is based on TD-error magnitude
        priority = (abs(td_error) + self.epsilon) ** self.alpha
        self.priorities.append(priority)
    
    def sample(self, batch_size):
        """Sample batch based on priorities"""
        if len(self.buffer) == 0:
            return None
        
        # Convert priorities to probabilities
        priorities = np.array(list(self.priorities))
        probabilities = priorities / priorities.sum()
        
        # Sample indices according to priority distribution
        indices = np.random.choice(len(self.buffer), size=batch_size, p=probabilities, replace=False)
        
        # Calculate importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
        weights = weights / weights.max()  # Normalize weights
        
        # Get samples
        samples = [self.buffer[i] for i in indices]
        
        return samples, indices, weights
    
    def update_priorities(self, indices, td_errors):
        """Update priorities based on new TD-errors"""
        for idx, td_error in zip(indices, td_errors):
            priority = (abs(td_error) + self.epsilon) ** self.alpha
            self.priorities[idx] = priority
    
    def __len__(self):
        return len(self.buffer)


class D3QAgent:
    """
    Dueling Double Deep Q-Learning Agent
    
    Features:
    - Dueling network architecture
    - Double Q-learning (reduces overestimation bias)
    - Prioritized experience replay
    - Gradient clipping
    - Target network with periodic updates
    """
    
    def __init__(self, state_size=28, action_size=4, learning_rate=0.0005,
                 gamma=0.95, epsilon=1.0, epsilon_min=0.15, epsilon_decay=0.99):
        
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.episode_count = 0  # Track episodes for adaptive epsilon
        
        # Device (CPU or GPU) - with fallback for compatibility
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        except:
            self.device = torch.device("cpu")
        print(f"Using device: {self.device}")
        
        # Main Q-Network and Target Network
        self.q_network = D3QNetwork(state_size, action_size).to(self.device)
        self.target_network = D3QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Loss function
        self.criterion = nn.SmoothL1Loss(reduction='none')  # Huber loss is more robust
        
        # Prioritized replay buffer
        self.replay_buffer = PrioritizedReplayBuffer(
            capacity=10000,
            alpha=0.6,  # Prioritization strength
            beta=0.4    # Importance sampling
        )
        
        # Batch size for training
        self.batch_size = 64
        
        # Target network update frequency
        self.target_update_freq = 100
        self.update_counter = 0
        
        # Current state for each robot
        self.current_states = {}
        self.current_actions = {}
        
        # Statistics
        self.episode_rewards = []
        self.losses = []
        
    def select_action(self, state, robot_id):
        """
        Select action using epsilon-greedy policy with obstacle awareness
        
        Args:
            state: Current state vector
            robot_id: ID of the robot
            
        Returns:
            action: Selected action (0-3)
        """
        # Store current state
        self.current_states[robot_id] = state
        
        # Check if robot is near obstacle (proximity sensors in state)
        # State format: [x, y, goal_x, goal_y, prox0, ..., prox23]
        proximity_sensors = state[4:]  # Last 24 values are proximity sensors
        max_proximity = max(proximity_sensors)
        
        # If very close to obstacle, force avoidance behavior
        if max_proximity > 0.6:
            # Emergency avoidance: choose turn action (not forward)
            # Find which side has less obstacle
            left_sensors = proximity_sensors[:12]
            right_sensors = proximity_sensors[12:]
            left_avg = sum(left_sensors) / len(left_sensors)
            right_avg = sum(right_sensors) / len(right_sensors)
            
            # Turn away from obstacles
            if left_avg > right_avg:
                action = 2  # Turn right (away from left obstacle)
            else:
                action = 1  # Turn left (away from right obstacle)
            
            self.current_actions[robot_id] = action
            return action
        
        # Adaptive epsilon based on episode count
        effective_epsilon = self.epsilon
        if self.episode_count < 30:
            effective_epsilon = max(0.5, self.epsilon)  # Keep high early
        
        # Epsilon-greedy action selection
        if np.random.rand() < effective_epsilon:
            # Explore: random action, but avoid forward if obstacle ahead
            if max_proximity > 0.4:
                # Don't move forward into obstacle
                action = np.random.choice([1, 2, 3])  # Only turn or stop
            else:
                action = np.random.randint(0, self.action_size)
        else:
            # Exploit: best action from Q-network
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
            
            # If obstacle ahead, mask out forward action
            if max_proximity > 0.4:
                q_values_np = q_values.cpu().numpy()[0]
                q_values_np[0] = -1000  # Make forward action very unattractive
                action = np.argmax(q_values_np)
            else:
                action = q_values.argmax().item()
        
        # Store current action
        self.current_actions[robot_id] = action
        
        return action
    
    def store_transition(self, robot_id, reward, next_state, done, td_error=1.0):
        """
        Store transition in replay buffer
        
        Args:
            robot_id: ID of the robot
            reward: Reward received
            next_state: Next state after action
            done: Whether episode is done
            td_error: TD-error for prioritization
        """
        if robot_id in self.current_states and robot_id in self.current_actions:
            state = self.current_states[robot_id]
            action = self.current_actions[robot_id]
            
            self.replay_buffer.push(state, action, reward, next_state, done, td_error)
    
    def train(self):
        """
        Train the D3Q-Network using prioritized experience replay
        
        Returns:
            loss: Training loss (or None if not enough samples)
        """
        # Check if enough samples in buffer
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        # Sample prioritized batch
        batch_data = self.replay_buffer.sample(self.batch_size)
        
        if batch_data is None:
            return None
        
        batch, indices, weights = batch_data
        
        # Unpack batch
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)
        
        # Current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Double Q-learning: use main network to select action, target network to evaluate
        with torch.no_grad():
            # Select actions using main network
            next_actions = self.q_network(next_states).argmax(dim=1, keepdim=True)
            # Evaluate actions using target network
            next_q_values = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            
            # Target Q-values
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute TD-errors for priority updates
        td_errors = (target_q_values - current_q_values.squeeze()).detach().cpu().numpy()
        
        # Compute weighted loss (Huber loss is more stable than MSE)
        loss = self.criterion(current_q_values.squeeze(), target_q_values)
        weighted_loss = (loss * weights).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        weighted_loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update priorities based on TD-errors
        self.replay_buffer.update_priorities(indices, td_errors)
        
        # Update target network periodically
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return weighted_loss.item()
    
    def save_model(self, filepath):
        """Save model weights"""
        try:
            torch.save({
                'q_network_state_dict': self.q_network.state_dict(),
                'target_network_state_dict': self.target_network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'episode_rewards': self.episode_rewards,
            }, filepath)
            print(f"Model saved to {filepath}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, filepath):
        """Load model weights"""
        try:
            if os.path.exists(filepath):
                checkpoint = torch.load(filepath, map_location=self.device)
                self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
                self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                self.epsilon = checkpoint['epsilon']
                self.episode_rewards = checkpoint['episode_rewards']
                print(f"Model loaded from {filepath}")
            else:
                print(f"No model found at {filepath}")
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def get_statistics(self):
        """Get training statistics"""
        return {
            'epsilon': self.epsilon,
            'buffer_size': len(self.replay_buffer),
            'avg_reward_last_100': np.mean(self.episode_rewards[-100:]) if self.episode_rewards else 0,
            'total_episodes': len(self.episode_rewards)
        }


if __name__ == "__main__":
    # Test the D3Q-Network
    print("Testing D3Q-Network...")
    
    agent = D3QAgent()
    
    # Test action selection
    test_state = np.random.rand(28)
    action = agent.select_action(test_state, robot_id=0)
    print(f"Selected action: {action}")
    
    # Test transition storage
    next_state = np.random.rand(28)
    agent.store_transition(robot_id=0, reward=1.0, next_state=next_state, done=False)
    
    print("D3Q-Network test completed successfully!")
