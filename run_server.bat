@echo off
REM Run Q-Network Server (Windows)

echo ================================================
echo   Starting Q-Learning Server
echo ================================================
echo.

cd python

REM Check if requirements are installed
python -c "import torch" 2>nul
if errorlevel 1 (
    echo PyTorch not found. Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo Starting Q-Network server on localhost:5555
echo Press Ctrl+C to stop
echo.

python q_server.py

pause
