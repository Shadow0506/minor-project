#!/bin/bash

# Test script for formation boundary feature with loop functions

echo "=========================================="
echo "Formation Boundary Test with Loop Functions"
echo "=========================================="
echo ""

# Kill any existing processes
echo "1. Cleaning up existing processes..."
pkill -9 -f "q_server.py|argos3" 2>/dev/null
sleep 1

# Start Python server in background
echo "2. Starting Q-Learning server..."
cd /home/shadow56/Desktop/minor-project
source venv/bin/activate
cd python
python q_server.py &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"
sleep 2

# Start ARGoS
echo "3. Starting ARGoS simulation..."
echo "   Watch for:"
echo "   - [LoopFunction] messages showing initial setup"
echo "   - [Robot] LEFT FORMATION AREA messages"
echo "   - [LoopFunction] Reset robot messages"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

cd /home/shadow56/Desktop/minor-project
argos3 -c experiments/q_swarm_experiment.argos

# Cleanup
echo ""
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null
pkill -9 -f "q_server.py|argos3" 2>/dev/null
echo "Done!"
