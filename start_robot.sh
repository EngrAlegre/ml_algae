#!/bin/bash
# AMLAC Robot Startup Script
# Activates virtual environment and runs the main robot controller

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv311_tf/bin/activate

# Set Python path to current directory
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Log startup
echo "=========================================="
echo "AMLAC Robot Starting..."
echo "Time: $(date)"
echo "Directory: $SCRIPT_DIR"
echo "Python: $(which python)"
echo "Python Version: $(python --version)"
echo "=========================================="

# Run the main robot controller
# Use unbuffered output for real-time logging
python -u main.py

# If we get here, the script exited
echo "Robot script exited with code: $?"
deactivate
