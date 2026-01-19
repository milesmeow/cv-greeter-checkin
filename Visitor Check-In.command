#!/bin/bash
# Visitor Check-In Application Launcher
# Double-click this file to start the application

# Change to the application directory
cd "$(dirname "$0")"

# Use Python directly from the conda environment
PYTHON="/usr/local/Caskroom/miniconda/base/envs/visitor-checkin/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "Error: Python not found at $PYTHON"
    echo "Make sure the visitor-checkin conda environment exists."
    echo "Press Enter to close..."
    read
    exit 1
fi

# Run the application
"$PYTHON" main.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press Enter to close this window..."
    read
fi
