import os
import subprocess
import time
from multiprocessing import Process, Event

class NetworkStatsCollector:
    def __init__(self):
        self.apps = {
            "com.Slack": "Slack_output.txt",
            "com.Discord": "Discord_output.txt",
            "com.RocketChat": "RocketChat_output.txt",
            "com.Microsoft.Teams": "Teams_output.txt",
            "com.textnow": "Textnow_output.txt",
            "com.facebook.orca": "Messenger_output.txt",
            "org.telegram.messenger": "Telegram_output.txt",
            "org.thoughtcrime.securesms": "Signal_output.txt",
            "com.snapchat.android": "Snapchat_output.txt",
            "com.whatsapp": "WhatsApp_output.txt"
        }

        self.unique_ports = set()
        self.unique_ips = set()
        self.excluded_ports = {'443'}
        self.stop_event = Event()
        self.process = None

    def capture_network_stats(self):
        """Capture network statistics for defined apps."""
        timestamp = time.strftime("%Y-%m-%d %T")
        for package, output_file in self.apps.items():
            command = f'adb shell netstat -p -n | grep "{package}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.stdout:
                with open(output_file, 'a') as f:
                    for line in result.stdout.splitlines():
                        f.write(f"{timestamp} {line}\n")

    def process_address(self, address_part):
        """Process address part and extract IP and port."""
        if ':' in address_part:
            ip_part, port_part = address_part.rsplit(':', 1)
            port = ''.join(filter(str.isdigit, port_part))
            if port and port not in self.excluded_ports:
                self.unique_ports.add(port)
            if ip_part:
                self.unique_ips.add(ip_part.split(':')[-1])

    def process_network_stats(self):
        """Process the captured network statistics to extract unique IPs and ports."""
        for output_file in self.apps.values():
            with open(output_file, 'r') as file:
                for line in file:
                    if 'tcp6' not in line and 'udp' not in line:
                        continue
                    parts = [part for part in line.split(' ') if part]
                    if len(parts) >= 7:
                        local_address_part = parts[5]
                        remote_address_part = parts[6]
                        self.process_address(local_address_part)
                        self.process_address(remote_address_part)

    def generate_wireshark_filter(self):
        """Generate Wireshark filter string from unique IPs and ports."""
        unique_ports_list = sorted(self.unique_ports, key=lambda x: int(x))
        unique_ips_list = sorted(self.unique_ips)

        ip_filters = [f"(ip.addr == {ip} or ipv6.addr == {ip})" for ip in unique_ips_list]
        port_filters = [f"(tcp.port == {port} or udp.port == {port})" for port in unique_ports_list]

        all_filters = ip_filters + port_filters
        return " or ".join(all_filters)

    def start_collecting(self):
        """Start the network statistics collection process."""
        while not self.stop_event.is_set():
            self.capture_network_stats()
            self.process_network_stats()
            wireshark_filter = self.generate_wireshark_filter()

            # Write the unique ports and IPs to their respective files
            with open("unique_ports.txt", 'w') as ports_file:
                ports_file.write("\n".join(sorted(self.unique_ports, key=int)) + "\n")
            
            with open("unique_ips.txt", 'w') as ips_file:
                ips_file.write("\n".join(sorted(self.unique_ips)) + "\n")
            
            # Write the Wireshark filter to a file
            with open("wireshark_filter.txt", 'w') as filter_file:
                filter_file.write(wireshark_filter + "\n")

            time.sleep(60)  # Adjust the interval as needed

    def start(self):
        """Start the background process."""
        self.process = Process(target=self.start_collecting)
        self.process.start()

    def stop(self):
        """Stop the background process."""
        if self.process:
            self.stop_event.set()
            self.process.join()
            self.process = None
            self.stop_event.clear()
