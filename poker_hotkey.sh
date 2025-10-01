#!/bin/bash
# Poker AI Analysis Hotkey Script
# This script activates the conda environment and runs the headless analysis
# Perfect for Keyboard Maestro automation

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Lock file to prevent multiple instances
LOCK_FILE="$SCRIPT_DIR/.poker_ai.lock"

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Another instance is already running (PID: $PID). Exiting."
        exit 1
    else
        # Stale lock file, remove it
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file with current PID
echo $$ > "$LOCK_FILE"

# Cleanup function to remove lock file on exit
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT INT TERM

# Activate conda environment and run analysis
source ~/miniconda3/bin/activate
conda activate poker
python run_analysis.py

# Exit code from python script
EXIT_CODE=$?

# Cleanup will happen automatically via trap
exit $EXIT_CODE
