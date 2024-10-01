#!/usr/bin/env python3
import os
import re
import ipaddress
import json
import argparse
import logging
import sys
import subprocess
from datetime import datetime
from collections import defaultdict

from packet_analyzer import PacketAnalyzer

# **Added: List of ports to exclude from filter generation**
excluded_ports = [443]

def split_ip_port(address):
    """
    Split an address string into IP and port.
    Handles IPv4, IPv6, and IPv4-mapped IPv6 addresses.

    Returns:
        tuple: (ip (str), port (int)) or (None, None) if parsing fails.
    """
    try:
        if address.startswith('::ffff:'):
            # IPv4-mapped IPv6 address, e.g., ::ffff:192.168.97.2:443
            ipv4_part, port_str = address.rsplit(':', 1)
            ipv4_address = ipv4_part.replace('::ffff:', '')
            return ipv4_address, int(port_str)
        elif address.startswith('['):
            # IPv6 address, e.g., [2001:0db8:85a3::8a2e:0370:7334]:443
            ip_part, port_str = address.rsplit(']:', 1)
            ipv6_address = ip_part.strip('[')
            return ipv6_address, int(port_str)
        else:
            # IPv4 address, e.g., 192.168.1.1:443
            ip_part, port_str = address.rsplit(':', 1)
            return ip_part, int(port_str)
    except Exception as e:
        logging.warning(f"Failed to split address '{address}': {e}")
        return None, None

def extract_ports_ips(logfile, portfile, sourceipfile_v4, sourceipfile_v6,
                     destipfile_v4, destipfile_v6, sessions_file, allipfile=None):
    """
    Extract unique ports and IPs from the log file and record port usage sessions.

    Args:
        logfile (str): Path to the log file.
        portfile (str): Path to save unique ports.
        sourceipfile_v4 (str): Path to save unique source IPv4 IPs.
        sourceipfile_v6 (str): Path to save unique source IPv6 IPs.
        destipfile_v4 (str): Path to save unique destination IPv4 IPs.
        destipfile_v6 (str): Path to save unique destination IPv6 IPs.
        sessions_file (str): Path to save port usage sessions (JSON).
        allipfile (str, optional): Path to save all unique IPs.
    """
    unique_ports = set()
    unique_source_ips_v4 = set()
    unique_source_ips_v6 = set()
    unique_destination_ips_v4 = set()
    unique_destination_ips_v6 = set()
    
    # **Modified: Use defaultdict to store multiple sessions per port**
    port_usage = defaultdict(list)  # port -> list of {'start_unix': int, 'end_unix': int}

    # **Added: Track last usage time per port to handle session gaps**
    last_usage = {}   # port -> last usage timestamp

    with open(logfile, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            # Example log format:
            # 2024-09-12 06:20:52 tcp        0      0 192.168.97.2:59895      52.157.5.65:443         ESTABLISHED 19934/com.skype.raider
            parts = re.split(r'\s+', line)
            if len(parts) < 7:
                logging.warning(f"Line {line_num}: Unrecognized format. Skipping line.")
                continue
            timestamp_str = f"{parts[0]} {parts[1]}"
            protocol = parts[2]
            recv_bytes = parts[3]
            sent_bytes = parts[4]
            src_address = parts[5]
            dst_address = parts[6]
            # **Extract application info if available**
            app_info = parts[7] if len(parts) > 7 else "unknown_app"
            app_name = sanitize_app_name(app_info.split('/')[-1])  # Extract application name

            # Process src and dst addresses
            src_ip, src_port = split_ip_port(src_address)
            dst_ip, dst_port = split_ip_port(dst_address)
            try:
                current_time = int(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timestamp())
            except ValueError as ve:
                logging.warning(f"Line {line_num}: Invalid timestamp '{timestamp_str}'. Skipping line.")
                continue

            # **Modified: Exclude ports in excluded_ports list**
            if src_ip and src_port and src_port not in excluded_ports:
                if is_ipv4(src_ip) and src_ip != "192.168.97.2":
                    unique_source_ips_v4.add(src_ip)
                else:
                    unique_source_ips_v6.add(src_ip)
                unique_ports.add(src_port)
                # **Handle session gaps of 15 minutes (900 seconds)**
                if src_port in last_usage:
                    if current_time - last_usage[src_port] > 900:
                        # Create a new session
                        port_usage[src_port].append({'start_unix': current_time, 'end_unix': current_time})
                        logging.debug(f"New session started for port {src_port} at {current_time}.")
                    else:
                        # Update the existing session's end time
                        port_usage[src_port][-1]['end_unix'] = current_time
                        logging.debug(f"Session updated for port {src_port} to {current_time}.")
                else:
                    # First usage of the port
                    port_usage[src_port].append({'start_unix': current_time, 'end_unix': current_time})
                    logging.debug(f"First session created for port {src_port} at {current_time}.")
                last_usage[src_port] = current_time  # Update last usage time

            if dst_ip and dst_port and dst_port not in excluded_ports:
                if is_ipv4(dst_ip):
                    unique_destination_ips_v4.add(dst_ip)
                else:
                    unique_destination_ips_v6.add(dst_ip)
                unique_ports.add(dst_port)
                # **Handle session gaps of 15 minutes (900 seconds)**
                if dst_port in last_usage:
                    if current_time - last_usage[dst_port] > 900:
                        # Create a new session
                        port_usage[dst_port].append({'start_unix': current_time, 'end_unix': current_time})
                        logging.debug(f"New session started for port {dst_port} at {current_time}.")
                    else:
                        # Update the existing session's end time
                        port_usage[dst_port][-1]['end_unix'] = current_time
                        logging.debug(f"Session updated for port {dst_port} to {current_time}.")
                else:
                    # First usage of the port
                    port_usage[dst_port].append({'start_unix': current_time, 'end_unix': current_time})
                    logging.debug(f"First session created for port {dst_port} at {current_time}.")
                last_usage[dst_port] = current_time  # Update last usage time

    # Save unique ports and IPs
    save_to_file(unique_ports, portfile)
    logging.info(f"Saved unique ports to '{portfile}'.")
    save_to_file(unique_source_ips_v4, sourceipfile_v4)
    logging.info(f"Saved unique source IPv4 IPs to '{sourceipfile_v4}'.")
    save_to_file(unique_source_ips_v6, sourceipfile_v6)
    logging.info(f"Saved unique source IPv6 IPs to '{sourceipfile_v6}'.")
    save_to_file(unique_destination_ips_v4, destipfile_v4)
    logging.info(f"Saved unique destination IPv4 IPs to '{destipfile_v4}'.")
    save_to_file(unique_destination_ips_v6, destipfile_v6)
    logging.info(f"Saved unique destination IPv6 IPs to '{destipfile_v6}'.")

    # Save all unique IPs if requested
    if allipfile:
        all_ips = unique_source_ips_v4.union(unique_source_ips_v6,
                                            unique_destination_ips_v4,
                                            unique_destination_ips_v6)
        save_to_file(all_ips, allipfile)
        logging.info(f"Saved all unique IPs to '{allipfile}'.")

    # Save port usage sessions
    save_sessions_to_json(port_usage, sessions_file)
    logging.info(f"Saved port usage sessions to '{sessions_file}'.")

def is_ipv4(address):
    """Check if the given address is IPv4."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        return False

def save_to_file(data_set, file_path):
    """Save a set of data to a file, one entry per line."""
    with open(file_path, 'w') as f:
        for item in sorted(data_set):
            f.write(f"{item}\n")

def save_sessions_to_json(port_usage, file_path):
    """Save port usage sessions to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(port_usage, f, indent=4)

def sanitize_app_name(app_name):
    """Sanitize application name to be filesystem-friendly."""
    return re.sub(r'\W+', '_', app_name)

def generate_port_filter(items, ip_version=None, port_filter=True):
    """
    Generate a Wireshark filter string for a set of items (IPs or ports).

    Args:
        items (set): Set of IPs or ports.
        ip_version (str, optional): 'IPv4' or 'IPv6'. Default is None.
        port_filter (bool): If True, items are ports. If False, IPs.

    Returns:
        str: Wireshark filter string.
    """
    if port_filter:
        # **Modified: Exclude ports in excluded_ports list**
        ports = sorted(set(items) - set(excluded_ports))
        if not ports:
            return ""
        ports_str = ','.join(str(port) for port in ports)
        print(f"ports_str: {ports_str}")
        return f"tcp.port in {{{ports_str}}}"
    else:
        # Items are IPs
        if ip_version == 'IPv4':
            ips = sorted(items)
            if not ips:
                return ""
            ips_str = ' or '.join(f"ip.addr == {ip}" for ip in ips)
            return ips_str
        elif ip_version == 'IPv6':
            ips = sorted(items)
            if not ips:
                return ""
            ips_str = ' or '.join(f"ipv6.addr == {ip}" for ip in ips)
            return ips_str
        else:
            return ""

def generate_exclusion_filter():
    """
    Generate exclusion filters to omit unwanted traffic (e.g., local traffic).

    Returns:
        str: Exclusion filter string.
    """
    # Example: Exclude traffic to/from localhost
    return "(ip.addr != 127.0.0.1) and (ipv6.addr != ::1)"

def generate_time_sensitive_filters(app_name, port_usage_sessions, ip_filter_v4, ip_filter_v6,
                                   port_filter, exclusion_filter, output_dir, merged_pcap):
    """
    Combine all filters and generate PCAP using tshark with time constraints.
    """
    sanitized_app_name = sanitize_app_name(app_name)
    combined_filters = []

    analyzer = PacketAnalyzer(capture_file=merged_pcap)
    results = analyzer.run_analysis()

    if sanitized_app_name == "Discord":
        app_name_for_filter = "discord"
    elif sanitized_app_name == "Messenger":
        app_name_for_filter = "facebook"
    elif sanitized_app_name == "Signal":
        app_name_for_filter = "signal"
    elif sanitized_app_name == "Skype":
        app_name_for_filter = "skype"
    elif sanitized_app_name == "Slack":
        app_name_for_filter = "slack"
    elif sanitized_app_name == "Teams":
        app_name_for_filter = "teams"
    elif sanitized_app_name == "RocketChat":
        app_name_for_filter = "rocket"
    elif sanitized_app_name == "Telegram":
        app_name_for_filter = "telegram"

    # Combine IP filters
    if ip_filter_v4:
        combined_filters.append(ip_filter_v4)
    if ip_filter_v6:
        combined_filters.append(ip_filter_v6)

    # Combine port filters
    if port_filter:
        combined_filters.append(port_filter)

    # Combine exclusion filters
    if exclusion_filter:
        combined_filters.append(exclusion_filter)

    # Base filter without time constraints
    base_filter = ' or '.join(combined_filters)

    # Initialize overall filter with time constraints
    overall_filter = ''

    # Iterate over each port and its usage sessions
    port_time_filters = []
    buffer = 60  # seconds buffer to capture relevant packets
    for port, sessions in port_usage_sessions.items():
        for session in sessions:
            start = session['start_unix'] - buffer - 89356
            end = session['end_unix'] + buffer - 89356
            # Create a filter for this port and time range
            port_time_filter = f"(tcp.port == {port} and frame.time_epoch >= {start} and frame.time_epoch <= {end})"
            port_time_filters.append(port_time_filter)

    if port_time_filters:
        # Combine all port-time filters with OR
        time_constraints = ' or '.join(port_time_filters)
        telegram_ips = ["149.154.167.91", "149.154.165.136", "149.154.167.92", "149.154.165.136", "149.154.167.92"]
        telegram_filter = " or ".join([f'ip.addr=={ip}' for ip in telegram_ips])
        # Final filter is base_filter AND (time_constraints)
        if base_filter:
            if app_name_for_filter == "telegram":
                overall_filter = f"({base_filter}) or ({time_constraints}) or ({telegram_filter})"
            else:
                overall_filter = f"({base_filter}) or ({time_constraints}) or ({results[app_name_for_filter]['wireshark_filter']})"
        else:
            if app_name_for_filter == "telegram":
                 overall_filter = f"({time_constraints}) or ({telegram_filter})"
            else:
                overall_filter = f"({time_constraints}) or ({results[app_name_for_filter]['wireshark_filter']})"
    else:
        # If no port-time filters, use base_filter
        overall_filter = base_filter

    # **Added: Exclude port 443 from the overall filter**
    # Since port 443 is already excluded during extraction and port_filter generation,
    # no additional exclusion is necessary here.

    # Write the combined filter to a file
    filter_filename = f"{sanitized_app_name}_combined_filter.txt"
    filter_file_path = os.path.join(output_dir, filter_filename)
    with open(filter_file_path, "w") as f:
        f.write(overall_filter)
    logging.info(f"Combined filter saved to '{filter_file_path}'.")

    # Generate PCAP using tshark with the combined filter
    pcap_filename = f"{sanitized_app_name}_filtered.pcap"
    pcap_file_path = os.path.join(output_dir, pcap_filename)

    try:
        logging.info(f"Generating PCAP '{pcap_file_path}' using tshark with filter.")
        subprocess.run([
            "tshark",
            "-r", merged_pcap,
            "-Y", overall_filter,
            "-w", pcap_file_path
        ], check=True)
        logging.info(f"Successfully created PCAP '{pcap_file_path}'.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create PCAP '{pcap_file_path}': {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Process ports and filters from log files and generate PCAPs."
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-commands')

    # Sub-command: extract
    extract_parser = subparsers.add_parser('extract', help='Extract ports and IPs from log files')
    extract_parser.add_argument('-l', '--logfile', type=str, required=True, help='Path to the log file')
    extract_parser.add_argument('-p', '--portfile', type=str, required=True, help='Path to save unique ports')
    extract_parser.add_argument('-s', '--sourceipfile_v4', type=str, required=True, help='Path to save unique source IPv4 IPs')
    extract_parser.add_argument('-s6', '--sourceipfile_v6', type=str, required=True, help='Path to save unique source IPv6 IPs')
    extract_parser.add_argument('-d4', '--destipfile_v4', type=str, required=True, help='Path to save unique destination IPv4 IPs')
    extract_parser.add_argument('-d6', '--destipfile_v6', type=str, required=True, help='Path to save unique destination IPv6 IPs')
    extract_parser.add_argument('-a', '--allipfile', type=str, help='Path to save all unique IPs')
    extract_parser.add_argument('-o', '--sessions_file', type=str, required=True, help='Path to save port usage sessions (JSON)')
    extract_parser.add_argument('--json', action='store_true', help='Export data to JSON files')
    extract_parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    extract_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # Sub-command: generate-filters
    filter_parser = subparsers.add_parser('generate-filters', help='Generate Wireshark filters and PCAPs')
    filter_parser.add_argument('-s4', '--sourceipfile_v4', type=str, required=True, help='Path to unique source IPv4 IPs')
    filter_parser.add_argument('-s6', '--sourceipfile_v6', type=str, required=True, help='Path to unique source IPv6 IPs')
    filter_parser.add_argument('-d4', '--destipfile_v4', type=str, required=True, help='Path to unique destination IPv4 IPs')
    filter_parser.add_argument('-d6', '--destipfile_v6', type=str, required=True, help='Path to unique destination IPv6 IPs')
    filter_parser.add_argument('-a', '--allipfile', type=str, help='Path to all unique IPs')
    filter_parser.add_argument('-p', '--portfile', type=str, required=True, help='Path to unique ports')
    filter_parser.add_argument('--sessions_file', type=str, required=True, help='Path to port usage sessions JSON file')
    filter_parser.add_argument('-o', '--output_dir', type=str, required=True, help='Directory to save filters and PCAPs')
    filter_parser.add_argument('--appname', type=str, required=True, help='Name of the application (used in filenames)')
    filter_parser.add_argument('--merged_pcap', type=str, required=True, help='Path to the merged PCAP file')
    filter_parser.add_argument('--json', action='store_true', help='Export data to JSON files')
    filter_parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    filter_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Configure logging
    log_level = logging.WARNING
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    if args.command == 'extract':
        logging.info(f"Starting extraction from '{args.logfile}'.")
        extract_ports_ips(
            logfile=args.logfile,
            portfile=args.portfile,
            sourceipfile_v4=args.sourceipfile_v4,
            sourceipfile_v6=args.sourceipfile_v6,
            destipfile_v4=args.destipfile_v4,
            destipfile_v6=args.destipfile_v6,
            sessions_file=args.sessions_file,
            allipfile=args.allipfile
        )
        logging.info("Extraction complete.")
    elif args.command == 'generate-filters':
        # Generate exclusion filter
        # exclusion_filter = generate_exclusion_filter()
        exclusion_filter = ""
        # Generate IPv4 filter
        try:
            with open(args.sourceipfile_v4, 'r') as f:
                source_ips_v4 = set(line.strip() for line in f if line.strip())
            with open(args.destipfile_v4, 'r') as f:
                dest_ips_v4 = set(line.strip() for line in f if line.strip())
            all_ips_v4 = source_ips_v4.union(dest_ips_v4)
            ip_filter_v4 = generate_port_filter(all_ips_v4, ip_version='IPv4', port_filter=False)
        except FileNotFoundError as fe:
            logging.error(f"IPv4 IP file not found: {fe}")
            sys.exit(1)

        # Generate IPv6 filter
        try:
            with open(args.sourceipfile_v6, 'r') as f:
                source_ips_v6 = set(line.strip() for line in f if line.strip())
            with open(args.destipfile_v6, 'r') as f:
                dest_ips_v6 = set(line.strip() for line in f if line.strip())
            all_ips_v6 = source_ips_v6.union(dest_ips_v6)
            # ip_filter_v6 = generate_port_filter(all_ips_v6, ip_version='IPv6', port_filter=False)
            ip_filter_v6 = ""
        except FileNotFoundError as fe:
            logging.error(f"IPv6 IP file not found: {fe}")
            sys.exit(1)

        # Optionally, generate all IPs
        if args.allipfile:
            try:
                all_ips = all_ips_v4.union(all_ips_v6)
                save_to_file(all_ips, args.allipfile)
                logging.info(f"Saved all unique IPs to '{args.allipfile}'.")
            except Exception as e:
                logging.error(f"Failed to save all IPs: {e}")
                sys.exit(1)

        # Generate Port filter
        try:
            with open(args.portfile, 'r') as f:
                ports = set(int(line.strip()) for line in f if line.strip())
            # **Modified: Exclude ports in excluded_ports list**
            ports = ports - set(excluded_ports)
            # port_filter = generate_port_filter(ports, port_filter=True)
            port_filter = ""
        except FileNotFoundError as fe:
            logging.error(f"Port file not found: {fe}")
            sys.exit(1)
        except ValueError as ve:
            logging.error(f"Invalid port number in port file: {ve}")
            sys.exit(1)

        # Load port usage sessions
        try:
            with open(args.sessions_file, 'r') as f:
                port_usage_sessions = json.load(f)
        except FileNotFoundError as fe:
            logging.error(f"Sessions file not found: {fe}")
            sys.exit(1)
        except json.JSONDecodeError as je:
            logging.error(f"Invalid JSON in sessions file: {je}")
            sys.exit(1)

        # Generate time-sensitive filters and create PCAPs
        generate_time_sensitive_filters(
            app_name=args.appname,
            port_usage_sessions=port_usage_sessions,
            ip_filter_v4=ip_filter_v4,
            ip_filter_v6=ip_filter_v6,
            port_filter=port_filter,
            exclusion_filter=exclusion_filter,
            output_dir=args.output_dir,
            merged_pcap=args.merged_pcap
        )

        logging.info("All time-sensitive filters have been generated and PCAPs created.")

if __name__ == "__main__":
    main()
