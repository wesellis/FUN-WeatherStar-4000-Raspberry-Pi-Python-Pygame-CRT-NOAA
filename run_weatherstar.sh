#!/bin/bash
# WeatherStar 4000 Launcher for Linux/Mac
# Make executable with: chmod +x run_weatherstar.sh

echo "Starting WeatherStar 4000..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed!"
    echo "Please install Python 3"
    exit 1
fi

# Run the launcher
python3 run_weatherstar.py