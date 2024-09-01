#!/bin/bash

# Define directories
# Define base directory
BASE_DIR=~/android_machine_ima/client/ima
AOSP_DIR=~/aosp/

# Define directories using the base directory
APK_DIR="$BASE_DIR/apks/"
INTERACTION_SCRIPTS_DIR="$BASE_DIR/interaction_scripts/"
COLLECT_PORTS_SCRIPT="$INTERACTION_SCRIPTS_DIR/collect_ports.sh"
START_TCPDUMP_SCRIPT="$INTERACTION_SCRIPTS_DIR/start_tcpdump.sh"
PYTHON_CLIENT=~/android_machine_ima/client/client.py

# Function to start the emulator
start_emulator() {
  cd "$AOSP_DIR" || exit
  source build/envsetup.sh
  lunch 16
  launch_cvd -daemon
  echo "Emulator launched, continuing with the script..."
}

# Function to wait for the emulator to boot
wait_for_boot() {
  adb wait-for-device
  timeout=300  # 5 minutes
  while [[ -z $(adb shell getprop sys.boot_completed | tr -d '\r') && $timeout -gt 0 ]]; do
    sleep 1
    ((timeout--))
  done
  if [ $timeout -eq 0 ]; then
    echo "Emulator boot timeout. Exiting."
    exit 1
  fi
}

# Function to install APKs
install_apks() {
  # Download files
  cd "$APK_DIR"
  download_file "1P1VsP6Vi1ft96rNdwDLjz7UnRVY5Z_3e"
  download_file "1RRkxAwtwTlZKLeqZ-IUnJHn2WWe-cVW0"
  download_file "1YKNj6ER1-JOWTeVPgGwrB2iWs4Drm6eZ"
  download_file "1ZmqG0bi17L-20GqpEf4cvSahhwvLlSrE"
  download_file "1_8x-aZWcMhaHRaF2bQu-IoSk_c1aIPkb"
  download_file "1_PTTnVGmYEtDNBVs-h0G6aaBFiPCj5q7"
  download_file "1_nuSa289S0d_2d5tdzjwGEMr17yvI5pj"
  download_file "1oTE9SK-xVXatyZGjsLuF8tqNpDrqTdkj"
  download_file "1vfF4ivMO08KZrK0GRM2q3AVaRnJOsM4P"
  download_file "1w1C_cLlSHhKhTzQkrL2FCXef9bJU2zAU"

  for apk in "$APK_DIR"/*.apk; do
    if [ -f "$apk" ]; then
      echo "Installing $apk"
      adb install "$apk"
      if [ $? -eq 0 ]; then
        echo "$apk installed successfully."
      else
        echo "Failed to install $apk."
      fi
    fi
  done
  cd ~
}

# Function to run interaction scripts
run_interaction_scripts() {
  if [ -d "$INTERACTION_SCRIPTS_DIR" ] && [ "$(ls -A "$INTERACTION_SCRIPTS_DIR")" ]; then
    for script in "$INTERACTION_SCRIPTS_DIR"/*.sh; do
      echo "Running $script..."
      timeout 60 ./"$script"  # Set a timeout of 60 seconds for each script
      if [ $? -ne 0 ]; then
        echo "Error: $script failed or timed out."
      fi
    done
  else
    echo "No interaction scripts found."
  fi
}

# Function to run data collection scripts
run_data_collection() {
  adb shell sh "$COLLECT_PORTS_SCRIPT"
  adb shell sh "$START_TCPDUMP_SCRIPT"
}

# Function to run the Python client
run_python_client() {
  if python3 "$PYTHON_CLIENT"; then
    echo "Python client ran successfully."
  else
    echo "Failed to run Python client."
  fi
}

download_file() {
  FILE_ID="$1"

  # Construct the Google Drive download link
  DOWNLOAD_LINK="https://drive.google.com/uc?id=${FILE_ID}"

  # Use gdown to download the file
  gdown "$DOWNLOAD_LINK"

  # Check if the download was successful
  if [ $? -ne 0 ]; then
      echo "Failed to download file with ID: $FILE_ID"
      exit 1
  fi
}

# Main script execution
start_emulator
wait_for_boot
install_apks
run_interaction_scripts
run_data_collection
run_python_client