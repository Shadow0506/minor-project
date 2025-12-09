#!/bin/bash

# Demo Learning Script - Prepare for Project Evaluation
# This script sets up a fresh learning demonstration

echo "======================================"
echo "DEMO LEARNING PREPARATION"
echo "======================================"
echo ""

# Backup current models
echo "[1/5] Backing up existing models..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f models/q_network_latest.pth ]; then
    cp models/q_network_latest.pth models/backup_${TIMESTAMP}.pth
    echo "✓ Backed up to models/backup_${TIMESTAMP}.pth"
else
    echo "  No existing model to backup"
fi

# Option to start fresh or continue
echo ""
read -p "Start with FRESH model (better for demo)? [Y/n]: " choice
choice=${choice:-Y}

if [[ "$choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo "[2/5] Starting fresh - removing old model..."
    rm -f models/q_network_latest.pth
    rm -f models/training_data.json
    echo "✓ Fresh start - bots will learn from scratch"
else
    echo ""
    echo "[2/5] Continuing with existing model..."
    echo "✓ Using existing learned weights"
fi

# Start the Q-Network server
echo ""
echo "[3/5] Starting Q-Network server..."
cd python
python3 q_server.py > ../logs/q_server_${TIMESTAMP}.log 2>&1 &
SERVER_PID=$!
cd ..

# Wait for server to initialize
echo "  Waiting for server to start..."
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✓ Q-Network server started (PID: $SERVER_PID)"
else
    echo "✗ Failed to start server - check logs/q_server_${TIMESTAMP}.log"
    exit 1
fi

echo ""
echo "[4/5] Ready to start ARGoS simulation"
echo ""
echo "======================================"
echo "DEMONSTRATION INSTRUCTIONS"
echo "======================================"
echo ""
echo "The bots will now learn collision avoidance and path planning."
echo ""
echo "What to expect in the first episodes:"
echo "  • Episodes 1-10: Random exploration, many collisions"
echo "  • Episodes 10-25: Learning to avoid immediate obstacles"
echo "  • Episodes 25-50: Coordinated movement toward goal"
echo "  • Episodes 50+: Refined navigation and formation"
echo ""
echo "Key improvements you'll see:"
echo "  1. Collision recovery - bots back up and turn away"
echo "  2. Progressive learning - fewer repeated mistakes"
echo "  3. Reward improvement - visible in terminal output"
echo ""
echo "======================================"
echo ""
echo "[5/5] Starting ARGoS simulation..."
echo ""

# Run ARGoS
argos3 -c experiments/q_swarm_experiment.argos

# Cleanup
echo ""
echo "Stopping Q-Network server..."
kill $SERVER_PID 2>/dev/null
echo "✓ Server stopped"

echo ""
echo "======================================"
echo "Demo complete! Check models/ for saved weights."
echo "======================================"
