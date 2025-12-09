"""
Deep Q-Network Implementation

This module implements a Deep Q-Learning network using PyTorch.
It includes:
- Neural network architecture
- Experience replay buffer
- Training logic
- Model saving/loading
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
import os


class DQN(nn.Module):
    """
    Deep Q-Network architecture
    
    Input: State vector [x, y, goal_x, goal_y, prox_0, ..., prox_23]
           Total size: 4 + 24 = 28
    Output: Q-values for 4 actions [forward, left, right, stop]
    """
    
    def __init__(self, state_size=28, action_size=4, hidden_size=128):
        super(DQN, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, action_size)
        
        self.relu = nn.ReLU()
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x


class ReplayBuffer:
    """
    Experience Replay Buffer
    
    Stores transitions (state, action, reward, next_state, done)
    for training the Q-Network
    """
    
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)


class QNetworkAgent:
    """
    Q-Learning Agent
    
    Manages the Q-Network, handles action selection,
    and performs learning updates.
    """
    
    def __init__(self, state_size=28, action_size=4, learning_rate=0.0005,
                 gamma=0.95, epsilon=1.0, epsilon_min=0.1, epsilon_decay=0.998):
        
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.episode_count = 0  # Track episodes for adaptive epsilon
        
        # Device (CPU or GPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Q-Network and Target Network
        self.q_network = DQN(state_size, action_size).to(self.device)
        self.target_network = DQN(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Loss function
        self.criterion = nn.MSELoss()
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(capacity=10000)
        
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
        Select action using epsilon-greedy policy with adaptive exploration
        
        Args:
            state: Current state vector
            robot_id: ID of the robot
            
        Returns:
            action: Selected action (0-3)
        """
        # Store current state
        self.current_states[robot_id] = state
        
        # Adaptive epsilon based on episode count (slower decay for first 50 episodes)
        effective_epsilon = self.epsilon
        if self.episode_count < 50:
            effective_epsilon = max(0.5, self.epsilon)  # Keep epsilon high during early learning
        
        # Epsilon-greedy action selection
        if np.random.rand() < effective_epsilon:
            # Explore: random action
            action = np.random.randint(0, self.action_size)
        else:
            # Exploit: best action from Q-network
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
            action = q_values.argmax().item()
        
        # Store current action
        self.current_actions[robot_id] = action
        
        return action
    
    def store_transition(self, robot_id, reward, next_state, done):
        """
        Store transition in replay buffer
        
        Args:
            robot_id: ID of the robot
            reward: Reward received
            next_state: Next state after action
            done: Whether episode is done
        """
        if robot_id in self.current_states and robot_id in self.current_actions:
            state = self.current_states[robot_id]
            action = self.current_actions[robot_id]
            
            self.replay_buffer.push(state, action, reward, next_state, done)
    
    def train(self):
        """
        Train the Q-Network using experience replay with prioritization
        
        Returns:
            loss: Training loss (or None if not enough samples)
        """
        # Check if enough samples in buffer
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        # Sample batch from replay buffer with prioritization for positive rewards
        all_samples = list(self.replay_buffer.buffer)
        
        # Separate positive and negative reward experiences
        positive_samples = [s for s in all_samples if s[2] > 0]  # reward > 0
        negative_samples = [s for s in all_samples if s[2] <= 0]
        
        # Sample with bias toward positive experiences (70% positive, 30% negative)
        # This helps the network learn successful behaviors faster
        batch = []
        if len(positive_samples) > 0:
            n_positive = min(int(self.batch_size * 0.7), len(positive_samples))
            n_negative = self.batch_size - n_positive
            batch.extend(random.sample(positive_samples, n_positive))
            if n_negative > 0 and len(negative_samples) > 0:
                batch.extend(random.sample(negative_samples, min(n_negative, len(negative_samples))))
        else:
            # Fall back to random sampling if no positive samples yet
            batch = self.replay_buffer.sample(min(self.batch_size, len(all_samples)))
        
        # Ensure we have a full batch
        while len(batch) < self.batch_size and len(all_samples) >= self.batch_size:
            batch.extend(random.sample(all_samples, self.batch_size - len(batch)))
        
        if len(batch) < self.batch_size:
            return None
        
        # Unpack batch
        states, actions, rewards, next_states, dones = zip(*batch)
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q-values from target network
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute loss
        loss = self.criterion(current_q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping to prevent exploding gradients
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        # Update target network periodically
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        return loss.item()
    
    def save_model(self, filepath):
        """Save model weights"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load model weights"""
        if os.path.exists(filepath):
            checkpoint = torch.load(filepath)
            self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
            self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epsilon = checkpoint['epsilon']
            self.episode_rewards = checkpoint['episode_rewards']
            print(f"Model loaded from {filepath}")
        else:
            print(f"No model found at {filepath}")
    
    def get_statistics(self):
        """Get training statistics"""
        return {
            'epsilon': self.epsilon,
            'buffer_size': len(self.replay_buffer),
            'avg_reward_last_100': np.mean(self.episode_rewards[-100:]) if self.episode_rewards else 0,
            'total_episodes': len(self.episode_rewards)
        }


if __name__ == "__main__":
    # Test the Q-Network
    print("Testing Q-Network...")
    
    agent = QNetworkAgent()
    
    # Test action selection
    test_state = np.random.rand(28)
    action = agent.select_action(test_state, robot_id=0)
    print(f"Selected action: {action}")
    
    # Test transition storage
    next_state = np.random.rand(28)
    agent.store_transition(robot_id=0, reward=1.0, next_state=next_state, done=False)
    
    print("Q-Network test completed successfully!")
