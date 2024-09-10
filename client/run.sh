#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# --- Variables ---
BASE_DIR=$(pwd)
CLIENT_DIR="$BASE_DIR"
VENV_DIR="$CLIENT_DIR/venv"
REQUIREMENTS_FILE="$CLIENT_DIR/requirements.txt"
APK_DIR="$BASE_DIR/../ima/apks"
VERBOSE=false

# --- Functions ---

# Display help menu
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --download-apks    Download APKs"
    echo "  --install-apks     Install APKs"
    echo "  --start-emulator   Start the Android emulator"
    echo "  --verbose          Display all command outputs"
    echo "  --help             Show this help message"
    echo
    echo "If no options are provided, the script will run with default behavior."
}

# Execute command with optional output suppression
run_command() {
    if $VERBOSE; then
        "$@"
    else
        "$@" &>/dev/null
    fi
}

# Check if a package is installed
package_installed() {
    dpkg -s "$1" &>/dev/null
}

# Install system packages
install_system_packages() {
    local packages=("python3-venv" "python3-pip")
    local to_install=()

    echo "Checking system packages..."
    for pkg in "${packages[@]}"; do
        if ! package_installed "$pkg"; then
            to_install+=("$pkg")
        fi
    done

    if [ ${#to_install[@]} -ne 0 ]; then
        echo "The following packages need to be installed: ${to_install[*]}"
        echo "Do you want to install them? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Installing packages..."
            run_command sudo apt update
            run_command sudo apt install -y "${to_install[@]}"
            echo "System packages installed successfully."
        else
            echo "Cannot proceed without necessary packages. Exiting."
            exit 1
        fi
    else
        echo "All necessary system packages are already installed."
    fi
}

# Setup and activate virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        run_command python3 -m venv "$VENV_DIR"
    fi

    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
}

# Install Python packages
install_python_packages() {
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "Installing Python packages from requirements.txt..."
        run_command pip install --upgrade pip
        run_command pip install -r "$REQUIREMENTS_FILE"
        echo "Python packages installed successfully."
    else
        echo "Warning: requirements.txt not found at $REQUIREMENTS_FILE"
        echo "Skipping Python package installation."
    fi
}

# Download APKs
download_apks() {
    echo "Preparing to download APKs..."
    mkdir -p "$APK_DIR"
    cd "$APK_DIR"
    
    if ! pip3 list | grep -q gdown; then
        echo "Installing gdown..."
        run_command pip3 install gdown
    fi
    
    file_ids=(
        "1P1VsP6Vi1ft96rNdwDLjz7UnRVY5Z_3e" "1RRkxAwtwTlZKLeqZ-IUnJHn2WWe-cVW0"
        "1YKNj6ER1-JOWTeVPgGwrB2iWs4Drm6eZ" "1ZmqG0bi17L-20GqpEf4cvSahhwvLlSrE"
        "1_8x-aZWcMhaHRaF2bQu-IoSk_c1aIPkb" "1_PTTnVGmYEtDNBVs-h0G6aaBFiPCj5q7"
        "1_nuSa289S0d_2d5tdzjwGEMr17yvI5pj" "1oTE9SK-xVXatyZGjsLuF8tqNpDrqTdkj"
        "1vfF4ivMO08KZrK0GRM2q3AVaRnJOsM4P" "1w1C_cLlSHhKhTzQkrL2FCXef9bJU2zAU"
    )
    
    echo "Downloading APKs..."
    for file_id in "${file_ids[@]}"; do
        echo "Downloading APK with ID: $file_id"
        run_command gdown "https://drive.google.com/uc?id=${file_id}"
    done
    
    echo "APK download completed."
    cd - > /dev/null
}

# Install APKs
install_apks() {
    echo "Preparing to install APKs..."
    local apk_count=$(ls -1 "$APK_DIR"/*.apk 2>/dev/null | wc -l)
    if [ "$apk_count" -eq 0 ]; then
        echo "No APKs found in $APK_DIR. Please download APKs first."
        return
    fi

    echo "Found $apk_count APKs to install."
    local installed=0
    for apk in "$APK_DIR"/*.apk; do
        if [ -f "$apk" ]; then
            echo "Installing $(basename "$apk")..."
            if run_command adb install "$apk"; then
                ((installed++))
            else
                echo "Failed to install $(basename "$apk")"
            fi
        fi
    done
    echo "Installation completed. $installed out of $apk_count APKs installed successfully."
}

# Start the emulator
start_emulator() {
    echo "Preparing to start emulator..."
    if [ ! -d ~/aosp ]; then
        echo "Error: AOSP directory not found. Please set up AOSP before starting the emulator."
        exit 1
    fi
    cd ~/aosp
    run_command source build/envsetup.sh
    run_command lunch 19
    echo "Launching emulator..."
    run_command launch_cvd --x_res=1080 --y_res=2340 --dpi=443 --cpus=2 --memory_mb=10240 --num_instances=1 --daemon
    echo "Waiting for device to be ready..."
    run_command adb wait-for-device
    run_command adb shell pm disable-user --user 0 com.android.inputmethod.latin
    echo "Emulator started and ready."
    cd - > /dev/null
}

# --- Main Execution ---

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --download-apks)
            DOWNLOAD_APKS=true
            shift
            ;;
        --install-apks)
            INSTALL_APKS=true
            shift
            ;;
        --start-emulator)
            START_EMULATOR=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Install system packages
install_system_packages

# Setup virtual environment
setup_venv

# Install Python packages
install_python_packages

# Execute requested actions
if [ "$DOWNLOAD_APKS" = true ]; then
    download_apks
fi

if [ "$INSTALL_APKS" = true ]; then
    install_apks
fi

if [ "$START_EMULATOR" = true ]; then
    start_emulator
fi

# Ensure device is connected
echo "Ensuring device is connected..."
run_command adb wait-for-device
run_command adb devices

# Run the client package
echo "Running client package..."
cd "$BASE_DIR/.."
SERVER_IP="35.185.235.215" python3 -m client.client

# Cleanup
deactivate
echo "Script execution completed successfully."