@echo off
REM Build Script for Q-Swarm Controller (Windows)
REM This script builds the C++ controller for ARGoS

echo ================================================
echo   Building Q-Swarm Controller for ARGoS
echo ================================================
echo.

REM Navigate to controller directory
cd controllers\q_swarm_controller

REM Create build directory if it doesn't exist
if not exist build mkdir build
cd build

echo [1/3] Configuring with CMake...
cmake ..
if errorlevel 1 (
    echo ERROR: CMake configuration failed
    echo Make sure ARGoS3 is installed and in your PATH
    pause
    exit /b 1
)
echo.

echo [2/3] Building with CMake...
cmake --build . --config Release
if errorlevel 1 (
    echo ERROR: Build failed
    echo Check the error messages above
    pause
    exit /b 1
)
echo.

echo [3/3] Verifying build...
if exist q_swarm_controller.dll (
    echo SUCCESS: Controller built successfully!
    echo Library: q_swarm_controller.dll
) else if exist Release\q_swarm_controller.dll (
    echo SUCCESS: Controller built successfully!
    echo Library: Release\q_swarm_controller.dll
) else (
    echo WARNING: Could not find output library
    echo Check the build directory manually
)
echo.

echo ================================================
echo   Build Complete!
echo ================================================
echo.
echo Next steps:
echo   1. Start Python server: python python\q_server.py
echo   2. Run ARGoS: argos3 -c experiments\q_swarm_experiment.argos
echo.

pause
