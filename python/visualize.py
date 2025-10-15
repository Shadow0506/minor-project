"""
Visualization and Analysis Tools

This script provides tools to visualize training progress
and analyze the learned Q-Network behavior.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os


def plot_training_curve(data_file="../models/training_data.json"):
    """Plot the training reward curve"""
    
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found. Run training first.")
        return
    
    # Load training data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    episode_rewards = data['episode_rewards']
    
    # Calculate moving average
    window_size = 50
    moving_avg = []
    for i in range(len(episode_rewards)):
        start_idx = max(0, i - window_size + 1)
        moving_avg.append(np.mean(episode_rewards[start_idx:i+1]))
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    # Plot raw rewards
    plt.subplot(1, 2, 1)
    plt.plot(episode_rewards, alpha=0.3, label='Episode Reward')
    plt.plot(moving_avg, label=f'Moving Average ({window_size} episodes)', linewidth=2)
    plt.xlabel('Episode')
    plt.ylabel('Total Reward')
    plt.title('Training Progress')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot reward distribution
    plt.subplot(1, 2, 2)
    plt.hist(episode_rewards, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Episode Reward')
    plt.ylabel('Frequency')
    plt.title('Reward Distribution')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    output_file = "../models/training_curve.png"
    plt.savefig(output_file, dpi=150)
    print(f"Plot saved to {output_file}")
    
    plt.show()


def analyze_statistics(data_file="../models/training_data.json"):
    """Print detailed statistics about training"""
    
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found. Run training first.")
        return
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    rewards = np.array(data['episode_rewards'])
    
    print("\n" + "=" * 60)
    print("TRAINING ANALYSIS")
    print("=" * 60)
    print(f"Total Episodes: {len(rewards)}")
    print(f"Final Epsilon: {data['final_epsilon']:.4f}")
    print(f"\nReward Statistics:")
    print(f"  Mean: {np.mean(rewards):.2f}")
    print(f"  Std Dev: {np.std(rewards):.2f}")
    print(f"  Min: {np.min(rewards):.2f}")
    print(f"  Max: {np.max(rewards):.2f}")
    print(f"  Median: {np.median(rewards):.2f}")
    print(f"\nLast 100 Episodes:")
    print(f"  Mean: {np.mean(rewards[-100:]):.2f}")
    print(f"  Max: {np.max(rewards[-100:]):.2f}")
    print(f"\nFirst 100 Episodes:")
    print(f"  Mean: {np.mean(rewards[:100]):.2f}")
    print(f"  Max: {np.max(rewards[:100]):.2f}")
    print(f"\nImprovement: {np.mean(rewards[-100:]) - np.mean(rewards[:100]):.2f}")
    print("=" * 60 + "\n")


def test_trained_model(model_file="../models/q_network_final.pth"):
    """Test the trained model (requires ARGoS to be running)"""
    
    if not os.path.exists(model_file):
        print(f"Error: {model_file} not found. Train a model first.")
        return
    
    from q_network import QNetworkAgent
    
    # Load trained agent
    agent = QNetworkAgent()
    agent.load_model(model_file)
    agent.epsilon = 0.0  # No exploration, pure exploitation
    
    print("\n" + "=" * 60)
    print("TESTING TRAINED MODEL")
    print("=" * 60)
    print(f"Model: {model_file}")
    print(f"Epsilon: {agent.epsilon} (exploitation mode)")
    print("\nReady to test. Start ARGoS simulation.")
    print("=" * 60 + "\n")


def compare_training_runs(*data_files):
    """Compare multiple training runs"""
    
    plt.figure(figsize=(12, 6))
    
    for i, data_file in enumerate(data_files):
        if not os.path.exists(data_file):
            print(f"Warning: {data_file} not found, skipping...")
            continue
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        rewards = data['episode_rewards']
        
        # Calculate moving average
        window_size = 50
        moving_avg = []
        for j in range(len(rewards)):
            start_idx = max(0, j - window_size + 1)
            moving_avg.append(np.mean(rewards[start_idx:j+1]))
        
        label = os.path.basename(data_file)
        plt.plot(moving_avg, label=label, linewidth=2)
    
    plt.xlabel('Episode')
    plt.ylabel('Average Reward')
    plt.title('Training Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_file = "../models/training_comparison.png"
    plt.savefig(output_file, dpi=150)
    print(f"Comparison plot saved to {output_file}")
    
    plt.show()


if __name__ == "__main__":
    import sys
    
    print("\n=== Q-Learning Visualization Tools ===\n")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "plot":
            plot_training_curve()
        elif sys.argv[1] == "stats":
            analyze_statistics()
        elif sys.argv[1] == "test":
            test_trained_model()
        elif sys.argv[1] == "compare":
            if len(sys.argv) > 2:
                compare_training_runs(*sys.argv[2:])
            else:
                print("Usage: python visualize.py compare <file1> <file2> ...")
        else:
            print("Unknown command. Use: plot, stats, test, or compare")
    else:
        print("Usage:")
        print("  python visualize.py plot     - Plot training curve")
        print("  python visualize.py stats    - Show statistics")
        print("  python visualize.py test     - Test trained model")
        print("  python visualize.py compare <files...> - Compare multiple runs")
        print("\nRunning default: plot")
        plot_training_curve()
