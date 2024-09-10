#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install necessary packages
install_packages() {
    echo "Some necessary packages are missing. Do you want to install them? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        sudo apt update
        sudo apt install -y python3-venv python3-pip
    else
        echo "Cannot proceed without necessary packages. Exiting."
        exit 1
    fi
}

# Check for necessary packages
if ! command_exists python3 || ! command_exists pip3; then
    install_packages
fi

# Define directories
BASE_DIR=$(pwd)
CLIENT_DIR="$BASE_DIR"
VENV_DIR="$CLIENT_DIR/venv"
REQUIREMENTS_FILE="$CLIENT_DIR/requirements.txt"
APK_DIR="$BASE_DIR/../ima/apks"

# Function to download APKs
download_apks() {
    echo "Downloading APKs..."
    mkdir -p "$APK_DIR"
    cd "$APK_DIR"
    
    # Check if gdown is installed
    if ! command_exists gdown; then
        echo "gdown is not installed. Installing..."
        pip3 install gdown
    fi
    
    # List of file IDs to download
    file_ids=(
        "1P1VsP6Vi1ft96rNdwDLjz7UnRVY5Z_3e"
        "1RRkxAwtwTlZKLeqZ-IUnJHn2WWe-cVW0"
        "1YKNj6ER1-JOWTeVPgGwrB2iWs4Drm6eZ"
        "1ZmqG0bi17L-20GqpEf4cvSahhwvLlSrE"
        "1_8x-aZWcMhaHRaF2bQu-IoSk_c1aIPkb"
        "1_PTTnVGmYEtDNBVs-h0G6aaBFiPCj5q7"
        "1_nuSa289S0d_2d5tdzjwGEMr17yvI5pj"
        "1oTE9SK-xVXatyZGjsLuF8tqNpDrqTdkj"
        "1vfF4ivMO08KZrK0GRM2q3AVaRnJOsM4P"
        "1w1C_cLlSHhKhTzQkrL2FCXef9bJU2zAU"
    )
    
    for file_id in "${file_ids[@]}"; do
        gdown "https://drive.google.com/uc?id=${file_id}"
    done
    
    cd - > /dev/null
}

# Function to install APKs
install_apks() {
    echo "Installing APKs..."
    for apk in "$APK_DIR"/*.apk; do
        if [ -f "$apk" ]; then
            echo "Installing $apk"
            adb install "$apk"
        fi
    done
}

# Function to start the emulator
start_emulator() {
    echo "Starting emulator..."
    if [ ! -d ~/aosp ]; then
        echo "AOSP directory not found. Please set up AOSP before starting the emulator."
        exit 1
    fi
    cd ~/aosp
    source build/envsetup.sh
    lunch 16
    launch_cvd -daemon
    adb wait-for-device
    adb shell pm disable-user --user 0 com.android.inputmethod.latin
    cd - > /dev/null
}

# Create and activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install requirements
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing requirements..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: requirements.txt not found at $REQUIREMENTS_FILE"
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --download-apks)
            download_apks
            shift
            ;;
        --install-apks)
            install_apks
            shift
            ;;
        --start-emulator)
            start_emulator
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the client package
echo "Running client package..."
cd "$BASE_DIR/.."
python3 -m client.client

# Deactivate virtual environment
deactivate

echo "Script execution completed."