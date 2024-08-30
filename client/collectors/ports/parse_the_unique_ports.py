# Define sets to store unique ports and IP addresses
unique_ports = set()
unique_ips = set()

# Optionally exclude common ports that may not be relevant for filtering
excluded_ports = {'443'}

# List of application-specific output files
files = [
    'Slack_output.txt', 'Discord_output.txt', 'RocketChat_output.txt',
    'Teams_output.txt', 'Textnow_output.txt', 'Messenger_output.txt',
    'Signal_output.txt', 'Snapchat_output.txt', 'Telegram_output.txt',
    'WhatsApp_output.txt'
]

# Function to process address part and extract IP and port
def process_address(address_part):
    if ':' in address_part:
        ip_part, port_part = address_part.rsplit(':', 1)
        # Remove any non-numeric characters from the port part
        port = ''.join(filter(str.isdigit, port_part))
        if port and port not in excluded_ports:
            unique_ports.add(port)
        if ip_part:
            unique_ips.add(ip_part.split(':')[-1])

# Iterate over each application's output file
for filename in files:
    # Open the file and read its contents
    with open(filename, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            
            # Skip lines that don't contain the expected data format
            if 'tcp6' not in line and 'udp' not in line:
                continue

            # Split the line by spaces and filter out empty strings
            parts = [part for part in line.split(' ') if part]

            # Extract the local and remote address parts
            local_address_part = parts[5]
            remote_address_part = parts[6]

            # Process both local and remote addresses
            process_address(local_address_part)
            process_address(remote_address_part)

# Convert the sets to lists and sort them
unique_ports_list = sorted(list(unique_ports), key=lambda x: int(x))
unique_ips_list = sorted(list(unique_ips))

# Print the unique ports and IPs
print("Unique ports:", unique_ports_list)
print("Unique IPs:", unique_ips_list)

# Creating a Wireshark filter for the unique IPs and ports
ip_filters = ["(ip.addr == " + ip + " or ipv6.addr == " + ip + ")" for ip in unique_ips_list if ':' in ip or '.' in ip]  # Adjusted for both IPv4 and IPv6
port_filters = ["(tcp.port == " + port + " or udp.port == " + port + ")" for port in unique_ports_list]

# Combining all filters with 'or' operator
all_filters = ip_filters + port_filters
wireshark_filter = " or ".join(all_filters)

# Print the Wireshark filter
print("\nWireshark filter:")
print(wireshark_filter)
