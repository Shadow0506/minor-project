"""
Q-Network Server

This script runs a socket server that communicates with the ARGoS
C++ controllers. It receives states, selects actions using the Q-Network,
and performs learning updates based on rewards.

Protocol:
- Receive: "STATE|robot_id|x|y|goal_x|goal_y|prox0|...|prox23"
- Send: "ACTION|action_id"
- Receive: "REWARD|robot_id|reward|done"
- Send: "ACK"
"""

import socket
import threading
import time
import numpy as np
import os
from q_network import QNetworkAgent


class QServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        
        # Initialize Q-Network agent
        self.agent = QNetworkAgent(
            state_size=28,  # 4 (position + goal) + 24 (proximity sensors)
            action_size=4,   # forward, left, right, stop
            learning_rate=0.001,
            gamma=0.99,
            epsilon=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995
        )
        
        # Episode tracking
        self.episode_count = 0
        self.episode_rewards = {i: 0.0 for i in range(4)}  # 4 robots
        self.episode_steps = {i: 0 for i in range(4)}
        
        # Training statistics
        self.total_steps = 0
        self.training_interval = 10  # Train every N steps
        
        # Model save directory
        self.model_dir = "../models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Load existing model if available
        model_path = os.path.join(self.model_dir, "q_network_latest.pth")
        self.agent.load_model(model_path)
        
    def start(self):
        """Start the server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        print("=" * 50)
        print("=== Q-Learning Server Started ===")
        print(f"Listening on {self.host}:{self.port}")
        print("=" * 50)
        print("Waiting for ARGoS to connect...\n")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[INFO] Connection from {address}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.start()
        
        except KeyboardInterrupt:
            print("\n[INFO] Server shutting down...")
            self.save_final_model()
        
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket):
        """Handle communication with a single robot controller"""
        try:
            while True:
                # Receive message
                data = client_socket.recv(4096).decode('utf-8').strip()
                
                if not data:
                    break
                
                # Parse and handle message
                response = self.process_message(data)
                
                # Send response
                if response:
                    client_socket.send((response + "\n").encode('utf-8'))
        
        except Exception as e:
            print(f"[ERROR] Client handler error: {e}")
        
        finally:
            client_socket.close()
    
    def process_message(self, message):
        """Process incoming message and return response"""
        parts = message.split('|')
        
        if not parts:
            return None
        
        msg_type = parts[0]
        
        if msg_type == "STATE":
            return self.handle_state(parts)
        
        elif msg_type == "REWARD":
            return self.handle_reward(parts)
        
        else:
            print(f"[WARNING] Unknown message type: {msg_type}")
            return None
    
    def handle_state(self, parts):
        """
        Handle STATE message
        Format: STATE|robot_id|x|y|goal_x|goal_y|prox0|...|prox23
        Returns: ACTION|action_id
        """
        try:
            robot_id = int(parts[1])
            state_values = [float(x) for x in parts[2:]]
            
            # Verify state size
            if len(state_values) != 28:
                print(f"[WARNING] Invalid state size: {len(state_values)} (expected 28)")
                return "ACTION|0"  # Default: move forward
            
            # Select action using Q-Network
            action = self.agent.select_action(state_values, robot_id)
            
            # Increment step counter
            self.total_steps += 1
            self.episode_steps[robot_id] += 1
            
            # Train periodically
            if self.total_steps % self.training_interval == 0:
                loss = self.agent.train()
                if loss is not None and self.total_steps % 100 == 0:
                    stats = self.agent.get_statistics()
                    print(f"[TRAIN] Step {self.total_steps} | "
                          f"Loss: {loss:.4f} | "
                          f"Epsilon: {stats['epsilon']:.4f} | "
                          f"Buffer: {stats['buffer_size']}")
            
            return f"ACTION|{action}"
        
        except Exception as e:
            print(f"[ERROR] Error handling state: {e}")
            return "ACTION|0"
    
    def handle_reward(self, parts):
        """
        Handle REWARD message
        Format: REWARD|robot_id|reward|done
        Returns: ACK
        """
        try:
            robot_id = int(parts[1])
            reward = float(parts[2])
            done = int(parts[3]) == 1
            
            # Get next state (will be provided in next STATE message)
            # For now, use current state as placeholder
            if robot_id in self.agent.current_states:
                next_state = self.agent.current_states[robot_id]
                self.agent.store_transition(robot_id, reward, next_state, done)
            
            # Update episode reward
            self.episode_rewards[robot_id] += reward
            
            # Handle episode completion
            if done:
                print(f"[EPISODE] Robot {robot_id} | "
                      f"Steps: {self.episode_steps[robot_id]} | "
                      f"Reward: {self.episode_rewards[robot_id]:.2f}")
                
                # Store episode reward
                self.agent.episode_rewards.append(self.episode_rewards[robot_id])
                
                # Reset episode tracking for this robot
                self.episode_rewards[robot_id] = 0.0
                self.episode_steps[robot_id] = 0
                
                # Increment episode count
                self.episode_count += 1
                
                # Save model periodically
                if self.episode_count % 25 == 0:
                    self.save_model()
                
                # Print statistics every 100 episodes
                if self.episode_count % 100 == 0:
                    self.print_statistics()
            
            return "ACK"
        
        except Exception as e:
            print(f"[ERROR] Error handling reward: {e}")
            return "ACK"
    
    def save_model(self):
        """Save the current model"""
        filepath = os.path.join(self.model_dir, f"q_network_episode_{self.episode_count}.pth")
        self.agent.save_model(filepath)
        
        # Also save as latest
        latest_path = os.path.join(self.model_dir, "q_network_latest.pth")
        self.agent.save_model(latest_path)
    
    def save_final_model(self):
        """Save the final model and statistics"""
        final_path = os.path.join(self.model_dir, "q_network_final.pth")
        self.agent.save_model(final_path)
        
        # Save training curve
        self.save_training_curve()
    
    def save_training_curve(self):
        """Save training curve data"""
        import json
        
        curve_data = {
            'episode_rewards': self.agent.episode_rewards,
            'total_episodes': self.episode_count,
            'final_epsilon': self.agent.epsilon
        }
        
        filepath = os.path.join(self.model_dir, "training_data.json")
        with open(filepath, 'w') as f:
            json.dump(curve_data, f, indent=2)
        
        print(f"[INFO] Training data saved to {filepath}")
    
    def print_statistics(self):
        """Print training statistics"""
        stats = self.agent.get_statistics()
        
        print("\n" + "=" * 60)
        print(f"STATISTICS (Episode {self.episode_count})")
        print("=" * 60)
        print(f"Total Steps: {self.total_steps}")
        print(f"Epsilon: {stats['epsilon']:.4f}")
        print(f"Buffer Size: {stats['buffer_size']}")
        print(f"Avg Reward (last 100): {stats['avg_reward_last_100']:.2f}")
        print(f"Total Episodes: {stats['total_episodes']}")
        print("=" * 60 + "\n")


def main():
    # Create and start server
    server = QServer(host='localhost', port=5555)
    server.start()


if __name__ == "__main__":
    main()
