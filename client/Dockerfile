# Use the tracer0tong/android-emulator as the base image
FROM tracer0tong/android-emulator:latest

# Set environment variables for the Android SDK and emulator
ENV ANDROID_HOME=/opt/android-sdk-linux \
    EMULATOR_NAME=android-19 \
    ARCH=x86
    
# Expose the necessary ports for ADB and VNC
EXPOSE 22 5037 5554 5555 5900

# Copy the script into the Docker container
COPY slack_interaction.sh /usr/local/bin/slack_interaction.sh
COPY client.py /usr/local/bin/client.py

# Make the scripts executable
RUN chmod +x /usr/local/bin/slack_interaction.sh

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

# Set the entry point to start the emulator, run the shell script, and execute the Python client
ENTRYPOINT ["sh", "-c", "start-emulator && adb wait-for-device && /usr/local/bin/slack_interaction.sh && python3 /usr/local/bin/client.py"]

# Start the emulator with specific parameters (customize as needed)
CMD ["-no-boot-anim", "-no-window", "-gpu", "off", "-memory", "2048", "-avd", "$EMULATOR_NAME"]

# Wait for the emulator to fully boot up (can be customized)
HEALTHCHECK --interval=30s --timeout=10s --retries=5 CMD adb shell getprop sys.boot_completed | grep -m 1 "1"
