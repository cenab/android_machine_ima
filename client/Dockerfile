# Use the tracer0tong/android-emulator as the base image
FROM tracer0tong/android-emulator:latest

# Set environment variables for the Android SDK and emulator
ENV ANDROID_HOME=/opt/android-sdk-linux \
    EMULATOR_NAME=android-19 \
    ARCH=x86 \
    APK_DIR=/apks

# Expose the necessary ports for ADB and VNC
# 22: Typically used for SSH access (though not used in this specific Dockerfile).
# 5037: Used by ADB (Android Debug Bridge) to communicate with the emulator.
# 5554 and 5555: Used for the emulator’s console and ADB connections.
# 5900: Used for VNC (Virtual Network Computing) to access the emulator’s GUI.
# 5000: Custom port for the Python client to communicate with the emulator.
EXPOSE 22 5037 5554 5555 5900 5000

# Copy interaction scripts into the Docker container
COPY ./commands/user_interaction_functions/*.sh /usr/local/bin/interaction_scripts/

# Create a directory for the interaction scripts
RUN mkdir -p /usr/local/bin/interaction_scripts

# Copy other necessary scripts into the Docker container
COPY ./collect_ports/collect_ports.sh /usr/local/bin/collect_ports.sh
COPY ./collection_tcp/start_tcpdump.sh /usr/local/bin/start_tcpdump.sh
COPY ./client.py /usr/local/bin/client.py

# Copy APK files into the container
COPY ./install_ima_apk/apks $APK_DIR

# Make the scripts executable
RUN chmod +x /usr/local/bin/*.sh /usr/local/bin/interaction_scripts/*.sh

# Install Python and additional tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    python3 \
    python3-pip \
    && apt-get clean

# Install Python dependencies
RUN pip3 install websockets json uuid asyncio

# Script to install all APKs in the specified directory
RUN for apk in $APK_DIR/*.apk; do \
      if [ -f "$apk" ]; then \
        echo "Installing $apk"; \
        adb install "$apk"; \
      fi; \
    done

# Set the entry point to start the emulator, wait for it to boot, run all interaction scripts, collect ports, start tcpdump, and finally execute the Python client
ENTRYPOINT ["sh", "-c", "start-emulator && adb wait-for-device && for script in /usr/local/bin/interaction_scripts/*.sh; do adb shell sh $script; done && adb shell 'sh /system/bin/collect_ports.sh' && adb shell 'sh /system/bin/start_tcpdump.sh' && python3 /usr/local/bin/client.py"]

# Start the emulator with specific parameters (customize as needed)
CMD ["-no-boot-anim", "-no-window", "-gpu", "off", "-memory", "2048", "-avd", "$EMULATOR_NAME"]

# Wait for the emulator to fully boot up (can be customized)
HEALTHCHECK --interval=30s --timeout=10s --retries=5 CMD adb shell getprop sys.boot_completed | grep -m 1 "1"
