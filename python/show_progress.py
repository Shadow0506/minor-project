#!/usr/bin/env python3
"""
Quick Learning Progress Viewer
Shows real-time learning statistics during demonstration
"""

import json
import os
import time
import sys

def show_progress():
    """Display learning progress in real-time"""
    
    model_dir = "../models"
    data_file = os.path.join(model_dir, "training_data.json")
    
    print("=" * 60)
    print("REAL-TIME LEARNING PROGRESS MONITOR")
    print("=" * 60)
    print("\nPress Ctrl+C to stop monitoring\n")
    
    last_episode_count = 0
    
    try:
        while True:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                episode_rewards = data.get('episode_rewards', [])
                
                if len(episode_rewards) > 0:
                    current_episodes = len(episode_rewards)
                    
                    # Only update if new episodes
                    if current_episodes > last_episode_count:
                        last_episode_count = current_episodes
                        
                        # Calculate statistics
                        recent_10 = episode_rewards[-10:] if len(episode_rewards) >= 10 else episode_rewards
                        recent_25 = episode_rewards[-25:] if len(episode_rewards) >= 25 else episode_rewards
                        
                        avg_10 = sum(recent_10) / len(recent_10)
                        avg_25 = sum(recent_25) / len(recent_25)
                        avg_all = sum(episode_rewards) / len(episode_rewards)
                        
                        best_reward = max(episode_rewards)
                        worst_reward = min(episode_rewards)
                        
                        # Clear screen
                        os.system('clear' if os.name == 'posix' else 'cls')
                        
                        print("=" * 60)
                        print("REAL-TIME LEARNING PROGRESS")
                        print("=" * 60)
                        print(f"\n📊 Episodes Completed: {current_episodes}")
                        print(f"\n📈 Reward Statistics:")
                        print(f"   Latest Episode:     {episode_rewards[-1]:>8.2f}")
                        print(f"   Average (Last 10):  {avg_10:>8.2f}")
                        print(f"   Average (Last 25):  {avg_25:>8.2f}")
                        print(f"   Average (All):      {avg_all:>8.2f}")
                        print(f"   Best Ever:          {best_reward:>8.2f}")
                        print(f"   Worst Ever:         {worst_reward:>8.2f}")
                        
                        # Show trend
                        if len(episode_rewards) >= 20:
                            first_10_avg = sum(episode_rewards[:10]) / 10
                            improvement = avg_10 - first_10_avg
                            trend = "📈 IMPROVING" if improvement > 0 else "📉 Need more training"
                            print(f"\n🎯 Learning Trend: {trend} ({improvement:+.2f})")
                        
                        # Show progress bar
                        if current_episodes < 100:
                            progress = int((current_episodes / 100) * 40)
                            bar = "█" * progress + "░" * (40 - progress)
                            print(f"\n⏳ Progress to 100 episodes:")
                            print(f"   [{bar}] {current_episodes}/100")
                        
                        # Learning phase
                        if current_episodes < 10:
                            phase = "🔍 Phase 1: Random Exploration"
                        elif current_episodes < 25:
                            phase = "🎓 Phase 2: Basic Collision Avoidance"
                        elif current_episodes < 50:
                            phase = "🚀 Phase 3: Goal-Directed Movement"
                        else:
                            phase = "⭐ Phase 4: Refined Navigation"
                        
                        print(f"\n{phase}")
                        print("\n" + "=" * 60)
                        print("Press Ctrl+C to stop monitoring")
                        print("=" * 60)
                
            else:
                print("\nWaiting for training data...")
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        print("=" * 60)

if __name__ == "__main__":
    show_progress()
