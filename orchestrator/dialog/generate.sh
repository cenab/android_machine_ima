#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define paths
PROJECT_ROOT=$(pwd)
VENV_DIR="$PROJECT_ROOT/venv"
GENERATE_SCRIPT="$PROJECT_ROOT/generate/generate_dialog.py"
SCHEDULE_SCRIPT="$PROJECT_ROOT/schedule/schedule_dialog.py"
INPUT_FILE="$PROJECT_ROOT/generate/in/example_hamlet.txt"
INTERMEDIATE_OUTPUT="$PROJECT_ROOT/generate/out/play_dialogue_hamlet.xlsx"
FINAL_OUTPUT="$PROJECT_ROOT/schedule/out/play_dialogue_hamlet_scheduled.xlsx"

# Create and activate virtual environment
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install requirements
pip install -r "$PROJECT_ROOT/requirements.txt"

# Run generate_dialog.py
echo "Running generate_dialog.py..."
python "$GENERATE_SCRIPT" "$INPUT_FILE" "$INTERMEDIATE_OUTPUT"

# Run schedule_dialog.py
echo "Running schedule_dialog.py..."
python "$SCHEDULE_SCRIPT" --file "$INTERMEDIATE_OUTPUT"

echo "Process completed. Final output: $FINAL_OUTPUT"

# Deactivate virtual environment
deactivate