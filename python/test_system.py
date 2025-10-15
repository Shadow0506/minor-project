"""
Test Script for Q-Learning System

This script tests individual components to verify the system is working correctly.
Run this before starting full training to catch any issues early.
"""

import sys
import os

def test_imports():
    """Test if all required Python packages are installed"""
    print("=" * 60)
    print("TEST 1: Checking Python Imports")
    print("=" * 60)
    
    try:
        import torch
        print(f"✓ PyTorch installed: {torch.__version__}")
        print(f"  Device available: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
    except ImportError:
        print("✗ PyTorch NOT installed")
        print("  Install with: pip install torch")
        return False
    
    try:
        import numpy
        print(f"✓ NumPy installed: {numpy.__version__}")
    except ImportError:
        print("✗ NumPy NOT installed")
        return False
    
    try:
        import matplotlib
        print(f"✓ Matplotlib installed: {matplotlib.__version__}")
    except ImportError:
        print("✗ Matplotlib NOT installed")
        return False
    
    print("")
    return True


def test_q_network():
    """Test Q-Network instantiation and forward pass"""
    print("=" * 60)
    print("TEST 2: Testing Q-Network")
    print("=" * 60)
    
    try:
        from q_network import QNetworkAgent
        import numpy as np
        
        # Create agent
        agent = QNetworkAgent()
        print("✓ Q-Network agent created")
        
        # Test state input
        test_state = np.random.rand(28)
        action = agent.select_action(test_state, robot_id=0)
        print(f"✓ Action selection works: action = {action}")
        
        # Test transition storage
        next_state = np.random.rand(28)
        agent.store_transition(0, 1.0, next_state, False)
        print(f"✓ Transition storage works: buffer size = {len(agent.replay_buffer)}")
        
        # Test training (after adding more samples)
        for i in range(65):
            s = np.random.rand(28)
            a = agent.select_action(s, i % 4)
            ns = np.random.rand(28)
            agent.store_transition(i % 4, np.random.randn(), ns, False)
        
        loss = agent.train()
        if loss is not None:
            print(f"✓ Training works: loss = {loss:.4f}")
        else:
            print("✓ Training works (insufficient samples for first train)")
        
    except Exception as e:
        print(f"✗ Q-Network test failed: {e}")
        return False
    
    print("")
    return True


def test_socket_server():
    """Test socket server (without connecting client)"""
    print("=" * 60)
    print("TEST 3: Testing Socket Server Setup")
    print("=" * 60)
    
    try:
        import socket
        
        # Try to create a socket on port 5555
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind(('localhost', 5555))
        test_socket.listen(1)
        print("✓ Can bind to port 5555")
        test_socket.close()
        
    except Exception as e:
        print(f"✗ Socket test failed: {e}")
        print("  Port 5555 might be in use")
        return False
    
    print("")
    return True


def test_file_structure():
    """Test if all required files exist"""
    print("=" * 60)
    print("TEST 4: Checking File Structure")
    print("=" * 60)
    
    required_files = [
        "q_network.py",
        "q_server.py",
        "visualize.py",
        "requirements.txt",
        "../controllers/q_swarm_controller/q_swarm_controller.h",
        "../controllers/q_swarm_controller/q_swarm_controller.cpp",
        "../controllers/q_swarm_controller/CMakeLists.txt",
        "../experiments/q_swarm_experiment.argos",
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} NOT FOUND")
            all_exist = False
    
    # Check if controller is built
    controller_paths = [
        "../controllers/q_swarm_controller/build/libq_swarm_controller.so",
        "../controllers/q_swarm_controller/build/q_swarm_controller.dll",
        "../controllers/q_swarm_controller/build/Release/q_swarm_controller.dll",
    ]
    
    controller_built = False
    for path in controller_paths:
        if os.path.exists(path):
            print(f"✓ Controller built: {path}")
            controller_built = True
            break
    
    if not controller_built:
        print("⚠ Controller not built yet")
        print("  Run: build.bat (Windows) or ./build.sh (Linux/Mac)")
    
    print("")
    return all_exist


def test_argos_installation():
    """Test if ARGoS is installed"""
    print("=" * 60)
    print("TEST 5: Checking ARGoS Installation")
    print("=" * 60)
    
    import subprocess
    
    try:
        result = subprocess.run(['argos3', '--version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ ARGoS installed: {version}")
            return True
        else:
            print("✗ ARGoS command failed")
            return False
    except FileNotFoundError:
        print("✗ ARGoS not found in PATH")
        print("  Make sure ARGoS3 is installed")
        return False
    except Exception as e:
        print(f"⚠ Could not check ARGoS: {e}")
        return False
    
    print("")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Q-LEARNING SYSTEM TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Python Imports", test_imports()))
    results.append(("Q-Network", test_q_network()))
    results.append(("Socket Server", test_socket_server()))
    results.append(("File Structure", test_file_structure()))
    results.append(("ARGoS Installation", test_argos_installation()))
    
    # Summary
    print("=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("")
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is ready to run.")
        print("\nNext steps:")
        print("  1. Start server: python q_server.py")
        print("  2. Run ARGoS: argos3 -c ../experiments/q_swarm_experiment.argos")
    else:
        print("⚠ Some tests failed. Please fix the issues above.")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Change to python directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    run_all_tests()
