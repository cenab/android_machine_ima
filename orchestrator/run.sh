#!/bin/bash

# Define paths
APP_DIR=~/android_machine_ima # Update this to the actual path of your app directory
VENV_DIR="$APP_DIR/venv"
REQUIREMENTS_FILE="$APP_DIR/requirements.txt"
SERVER_FILE="$APP_DIR/server/server.py"
ORCHESTRATOR_FILE="$APP_DIR/orchestrator.py"

# Function to install system dependencies
install_system_dependencies() {
  echo "Updating system packages..."
  sudo apt-get update
  
  echo "Installing system dependencies..."
  sudo apt-get install -y python3 python3-pip python3-venv
  
  if [ $? -ne 0 ]; then
    echo "Failed to install system dependencies."
    exit 1
  fi
}

# Function to create and activate virtual environment
setup_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi
  echo "Activating virtual environment..."
  source "$VENV_DIR/bin/activate"
}

# Function to install Python requirements from requirements.txt
install_requirements() {
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing requirements from $REQUIREMENTS_FILE..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
      echo "Failed to install requirements."
      exit 1
    fi
  else
    echo "No requirements.txt file found."
  fi
}

# Function to run the server
run_server() {
  echo "Starting the server..."
  python "$SERVER_FILE" &
  SERVER_PID=$!
  echo "Server started with PID $SERVER_PID"
  sleep 5  # Give the server some time to initialize
}

# Function to run the orchestrator
run_orchestrator() {
  echo "Starting the orchestrator..."
  python "$ORCHESTRATOR_FILE" &
  ORCHESTRATOR_PID=$!
  echo "Orchestrator started with PID $ORCHESTRATOR_PID"
}

# Function to handle script termination
cleanup() {
  echo "Terminating server and orchestrator..."
  kill $SERVER_PID $ORCHESTRATOR_PID
  deactivate
  exit 0
}

# Set up trap to call cleanup function on script termination
trap cleanup SIGINT SIGTERM

# Main script execution
install_system_dependencies
setup_venv
install_requirements
run_server
run_orchestrator

# Keep the script running
echo "Press Ctrl+C to terminate the server and orchestrator."
while true; do
  sleep 1
done