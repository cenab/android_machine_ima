#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define paths
DIALOG_DIR=$(pwd)
PROJECT_ROOT=$(dirname "$DIALOG_DIR")
GENERATE_SCRIPT="$DIALOG_DIR/generate/generate_dialog.py"
SCHEDULE_SCRIPT="$DIALOG_DIR/schedule/schedule_dialog.py"
INPUT_FILE="$DIALOG_DIR/generate/in/example_hamlet.txt"
INTERMEDIATE_OUTPUT="$DIALOG_DIR/generate/out/play_dialogue_hamlet.xlsx"
FINAL_OUTPUT="$DIALOG_DIR/schedule/out/play_dialogue_hamlet_scheduled.xlsx"

# Create necessary directories
mkdir -p "$DIALOG_DIR/generate/out"
mkdir -p "$DIALOG_DIR/schedule/in"
mkdir -p "$DIALOG_DIR/schedule/out"

# Upgrade pip and install requirements
echo "Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r "$DIALOG_DIR/requirements.txt"

# Run generate_dialog.py
echo "Running generate_dialog.py..."
python3 "$GENERATE_SCRIPT" -i "$INPUT_FILE" -o "$INTERMEDIATE_OUTPUT"

# Run schedule_dialog.py
echo "Running schedule_dialog.py..."
python3 "$SCHEDULE_SCRIPT" --file "$INTERMEDIATE_OUTPUT" -o "$(basename "$FINAL_OUTPUT")"

echo "Process completed. Final output: $FINAL_OUTPUT"