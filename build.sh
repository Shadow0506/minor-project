#!/bin/bash
# Build Script for Q-Swarm Controller (Linux/Mac)

echo "================================================"
echo "  Building Q-Swarm Controller for ARGoS"
echo "================================================"
echo ""

# Navigate to controller directory
cd controllers/q_swarm_controller

# Create build directory if it doesn't exist
mkdir -p build
cd build

echo "[1/3] Configuring with CMake..."
cmake ..
if [ $? -ne 0 ]; then
    echo "ERROR: CMake configuration failed"
    echo "Make sure ARGoS3 is installed"
    exit 1
fi
echo ""

echo "[2/3] Building..."
make
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi
echo ""

echo "[3/3] Verifying build..."
if [ -f "libq_swarm_controller.so" ]; then
    echo "SUCCESS: Controller built successfully!"
    echo "Library: libq_swarm_controller.so"
elif [ -f "libq_swarm_controller.dylib" ]; then
    echo "SUCCESS: Controller built successfully!"
    echo "Library: libq_swarm_controller.dylib"
else
    echo "WARNING: Could not find output library"
fi
echo ""

echo "================================================"
echo "  Build Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Start Python server: python python/q_server.py"
echo "  2. Run ARGoS: argos3 -c experiments/q_swarm_experiment.argos"
echo ""
