@echo off
REM Run ARGoS Simulation (Windows)

echo ================================================
echo   Launching ARGoS Simulation
echo ================================================
echo.

REM Check if server is running
echo Make sure the Q-Network server is running!
echo If not, run: run_server.bat
echo.
timeout /t 3

cd experiments

echo Starting ARGoS...
argos3 -c q_swarm_experiment.argos

if errorlevel 1 (
    echo.
    echo ERROR: ARGoS failed to start
    echo.
    echo Possible issues:
    echo   1. ARGoS3 not installed or not in PATH
    echo   2. Controller library not built (run build.bat)
    echo   3. Q-Network server not running (run run_server.bat)
    echo.
)

pause
