#!/bin/bash

# Quick Pre-Demo Test
# Run this tonight to verify everything works

echo "==========================================="
echo "PRE-DEMO VERIFICATION TEST"
echo "==========================================="
echo ""

ERRORS=0

# Test 1: Controller library exists
echo "[1/7] Checking controller library..."
if [ -f "controllers/q_swarm_controller/build/libq_swarm_controller.so" ]; then
    echo "✓ Controller library found"
else
    echo "✗ Controller library missing - run: cd controllers/q_swarm_controller/build && make"
    ERRORS=$((ERRORS + 1))
fi

# Test 2: Python dependencies
echo ""
echo "[2/7] Checking Python dependencies..."
python3 -c "import torch; import numpy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Python dependencies OK"
else
    echo "✗ Missing dependencies - run: pip3 install torch numpy"
    ERRORS=$((ERRORS + 1))
fi

# Test 3: ARGoS experiment file
echo ""
echo "[3/7] Checking ARGoS configuration..."
if [ -f "experiments/q_swarm_experiment.argos" ]; then
    echo "✓ ARGoS experiment file found"
else
    echo "✗ ARGoS experiment file missing"
    ERRORS=$((ERRORS + 1))
fi

# Test 4: Demo script
echo ""
echo "[4/7] Checking demo script..."
if [ -x "demo_learning.sh" ]; then
    echo "✓ Demo script is executable"
else
    echo "✗ Demo script not executable - run: chmod +x demo_learning.sh"
    ERRORS=$((ERRORS + 1))
fi

# Test 5: Progress monitor
echo ""
echo "[5/7] Checking progress monitor..."
if [ -x "python/show_progress.py" ]; then
    echo "✓ Progress monitor is executable"
else
    echo "✗ Progress monitor not executable - run: chmod +x python/show_progress.py"
    ERRORS=$((ERRORS + 1))
fi

# Test 6: Logs directory
echo ""
echo "[6/7] Checking logs directory..."
if [ -d "logs" ]; then
    echo "✓ Logs directory exists"
else
    echo "✗ Logs directory missing - run: mkdir logs"
    ERRORS=$((ERRORS + 1))
fi

# Test 7: Models directory
echo ""
echo "[7/7] Checking models directory..."
if [ -d "models" ]; then
    echo "✓ Models directory exists"
else
    echo "✗ Models directory missing - run: mkdir models"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "==========================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - READY FOR DEMO!"
    echo "==========================================="
    echo ""
    echo "Quick test recommendation:"
    echo "  1. Start server: cd python && python3 q_server.py &"
    echo "  2. Wait 3 seconds"
    echo "  3. Run: argos3 -c experiments/q_swarm_experiment.argos"
    echo "  4. Let it run for 5 episodes"
    echo "  5. Stop with Ctrl+C"
    echo "  6. Kill server: pkill -f q_server"
    echo ""
    echo "If that works, you're 100% ready for tomorrow!"
else
    echo "❌ FOUND $ERRORS ERROR(S) - FIX BEFORE DEMO"
    echo "==========================================="
fi
echo ""
