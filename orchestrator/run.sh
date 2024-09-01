#!/bin/bash

# Define paths
APP_DIR=~/path/to/app  # Update this to the actual path of your app directory
REQUIREMENTS_FILE="$APP_DIR/requirements.txt"
SERVER_FILE="$APP_DIR/server.py"

# Function to install pip if not installed
install_pip() {
  if ! command -v pip &> /dev/null; then
    echo "pip not found. Installing pip..."
    sudo apt-get install python3-pip -y  # Adjust this command based on your OS
    if [ $? -ne 0 ]; then
      echo "Failed to install pip."
      exit 1
    fi
  else
    echo "pip is already installed."
  fi
}

# Function to install Python requirements from requirements.txt
install_requirements() {
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing requirements from $REQUIREMENTS_FILE..."
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
  python3 "$SERVER_FILE" &
  if [ $? -ne 0 ]; then
    echo "Failed to start the server."
    exit 1
  fi
}

# Main script execution
install_pip
install_requirements
run_server