import subprocess
import time
import uuid

class TcpDumpManager:
    def __init__(self):
        self.process = None  # To store the process object

    def run_command(self, command):
        """Run a shell command and handle its output."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Command succeeded: {command}")
            print(result.stdout)
        else:
            print(f"Command failed: {command}")
            print(result.stderr)

    def gain_root_access(self):
        """Gain root access on the device."""
        self.run_command("adb root")

    def check_current_user(self):
        """Check the current user on the device."""
        self.run_command("adb shell whoami")

    def remount_file_system(self):
        """Remount the file system as writable."""
        self.run_command("adb remount")

    def change_tcpdump_permissions(self):
        """Change permissions of the tcpdump binary."""
        # Updating the path to the tcpdump binary
        self.run_command("adb shell chmod 6755 /data/local/tmp/tcpdump")

    def start_tcpdump(self):
        """Start tcpdump to capture all network traffic in the background."""
        
        # Generate a UUID for the filename to ensure uniqueness
        unique_id = uuid.uuid4()
        file_name = f"/sdcard/imas_all_tcpdump_{unique_id}.pcap"
        
        # Command to start tcpdump with the generated file name
        command = f"adb shell /data/local/tmp/tcpdump -i any -s 0 -w {file_name}"
        
        try:
            # Start tcpdump as a background process
            self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Started tcpdump as a background process with PID: {self.process.pid}")

            # Wait for a short duration to ensure tcpdump starts properly
            time.sleep(2)

            # Check if tcpdump started successfully
            if self.process.poll() is None:  # If the process is still running
                print(f"tcpdump is running with PID: {self.process.pid} and output file: {file_name}")
            else:
                stderr_output = self.process.stderr.read().decode()
                print(f"Failed to start tcpdump. Error: {stderr_output}")

        except Exception as e:
            print(f"An error occurred while starting tcpdump: {e}")

    def stop_tcpdump(self):
        """Stop the tcpdump process if it's running."""
        if self.process and self.process.poll() is None:  # Check if process is still running
            self.process.terminate()
            print(f"Stopped tcpdump process with PID: {self.process.pid}")
            self.process = None
        else:
            print("No tcpdump process is currently running.")

    def run_tcpdump(self):
        """Run the full tcpdump setup process and start capturing."""
        self.gain_root_access()
        self.check_current_user()
        self.remount_file_system()
        self.change_tcpdump_permissions()
        self.start_tcpdump()
