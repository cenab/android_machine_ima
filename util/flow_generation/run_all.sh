#!/bin/bash
# ==============================================================================
# Script Name: run_all.sh
# Description: Automates the extraction of ports and IPs from log files,
#              generates port usage sessions, creates time-sensitive Wireshark
#              filters, and applies them to a merged PCAP file.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Function to display usage instructions
usage() {
    echo "Usage: $0 -m <merged_pcap> -r <raw_logs_dir> -b <base_output_dir> -o <global_output_dir>"
    echo
    echo "Options:"
    echo "  -m, --merged_pcap        Path to the merged PCAP file (e.g., ../ima_client_3_pcap/ima_client_3_pcap_output.pcap)"
    echo "  -r, --raw_logs_dir       Directory containing raw log files (e.g., raw/)"
    echo "  -b, --base_output_dir    Base directory where extraction outputs are stored (e.g., output/)"
    echo "  -o, --global_output_dir  Base directory for all outputs (default: 'final_output')"
    echo "  -h, --help               Display this help message and exit"
    exit 1
}

# Initialize variables with default values
GLOBAL_OUTPUT_DIR="final_output"

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m|--merged_pcap)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                MERGED_PCAP="$2"
                shift 2
            else
                echo "Error: --merged_pcap requires a non-empty argument."
                usage
            fi
            ;;
        -r|--raw_logs_dir)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                RAW_LOGS_DIR="$2"
                shift 2
            else
                echo "Error: --raw_logs_dir requires a non-empty argument."
                usage
            fi
            ;;
        -b|--base_output_dir)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                BASE_OUTPUT_DIR="$2"
                shift 2
            else
                echo "Error: --base_output_dir requires a non-empty argument."
                usage
            fi
            ;;
        -o|--global_output_dir)
            if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                GLOBAL_OUTPUT_DIR="$2"
                shift 2
            else
                echo "Error: --global_output_dir requires a non-empty argument."
                usage
            fi
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown parameter passed: $1"
            usage
            ;;
    esac
done

# Check if all required arguments are provided
if [[ -z "$MERGED_PCAP" || -z "$RAW_LOGS_DIR" || -z "$BASE_OUTPUT_DIR" ]]; then
    echo "Error: Missing required arguments."
    usage
fi

# Verify that the merged PCAP file exists
if [[ ! -f "$MERGED_PCAP" ]]; then
    echo "Error: Merged PCAP file '$MERGED_PCAP' does not exist."
    exit 1
fi

# Verify that the raw logs directory exists
if [[ ! -d "$RAW_LOGS_DIR" ]]; then
    echo "Error: Raw logs directory '$RAW_LOGS_DIR' does not exist."
    exit 1
fi

# Create base output and global output directories if they don't exist
mkdir -p "$BASE_OUTPUT_DIR"
mkdir -p "$GLOBAL_OUTPUT_DIR"

# Define the path to the Python processing script
PROCESS_SCRIPT="$(dirname "$0")/process_ports_filters.py"

# Verify that the Python script exists
if [[ ! -f "$PROCESS_SCRIPT" ]]; then
    echo "Error: Python processing script '$PROCESS_SCRIPT' does not exist."
    exit 1
fi

# Ensure the Python script is executable
chmod +x "$PROCESS_SCRIPT"

# Iterate through each merged_*_output_complete.txt file in raw/
shopt -s nullglob
raw_files=("${RAW_LOGS_DIR}"/merged_*_output_complete.txt)

for raw_file in "${raw_files[@]}"; do
    # Extract the application name, e.g., merged_Discord_output_complete.txt -> Discord
    filename="$(basename "${raw_file}")"
    app_name="$(echo "${filename}" | sed -E 's/^merged_(.+)_output_complete\.txt$/\1/')"

    echo "Processing application: ${app_name}"
    echo "--------------------------------------------"

    # Define the output directory for this application
    app_output_dir="${BASE_OUTPUT_DIR}/merged_${app_name}_output_complete_outputs"
    mkdir -p "${app_output_dir}"

    # Define log file path
    log_file="${app_output_dir}/merged_${app_name}_output_complete.log"

    # Define output file paths
    portfile="${app_output_dir}/merged_${app_name}_output_complete_ports.txt"
    sourceipfile_v4="${app_output_dir}/merged_${app_name}_output_complete_source_ips_v4.txt"
    sourceipfile_v6="${app_output_dir}/merged_${app_name}_output_complete_source_ips_v6.txt"
    destipfile_v4="${app_output_dir}/merged_${app_name}_output_complete_dest_ips_v4.txt"
    destipfile_v6="${app_output_dir}/merged_${app_name}_output_complete_dest_ips_v6.txt"
    allipfile="${app_output_dir}/merged_${app_name}_output_complete_all_ips.txt"
    sessions_file="${app_output_dir}/port_usage_sessions.json"

    # Run extraction
    echo "Running extraction for '${app_name}'..."
    python3 "$PROCESS_SCRIPT" extract \
        -l "$raw_file" \
        -p "$portfile" \
        -s "$sourceipfile_v4" \
        -s6 "$sourceipfile_v6" \
        -d4 "$destipfile_v4" \
        -d6 "$destipfile_v6" \
        -a "$allipfile" \
        -o "$sessions_file" \
        --json \
        --verbose \
        --debug \
        >> "$log_file" 2>&1

    echo "Extraction complete for '${app_name}'. Logs saved to '$log_file'."

    # Define filter output directory
    app_filter_output_dir="${GLOBAL_OUTPUT_DIR}/merged_${app_name}_filters"
    mkdir -p "$app_filter_output_dir"

    # Generate filters and PCAPs using the Python script
    echo "Generating filters and PCAPs for '${app_name}'..."
    python3 "$PROCESS_SCRIPT" generate-filters \
        -s4 "$sourceipfile_v4" \
        -s6 "$sourceipfile_v6" \
        -d4 "$destipfile_v4" \
        -d6 "$destipfile_v6" \
        -a "$allipfile" \
        -p "$portfile" \
        --sessions_file "$sessions_file" \
        -o "$app_filter_output_dir" \
        --appname "$app_name" \
        --merged_pcap "$MERGED_PCAP" \
        --json \
        --verbose \
        --debug \
        >> "$log_file" 2>&1

    echo "Filter generation and PCAP creation complete for '${app_name}'."
    echo "--------------------------------------------"
done

# Disable nullglob
shopt -u nullglob

echo "==============================================="
echo "All applications have been processed."
echo "Proceeding to apply Wireshark filters to the merged PCAP file..."
echo "==============================================="

# Apply filters using tshark
for filter_dir in "${GLOBAL_OUTPUT_DIR}"/merged_*_filters; do
    if [ -d "$filter_dir" ]; then
        app_name="$(echo "$(basename "$filter_dir")" | sed -E 's/^merged_(.+)_filters$/\1/')"
        echo "Applying aggregated filter for application: ${app_name}"

        # Define output PCAP path
        pcap_filename="${app_name}_filtered.pcap"
        pcap_output_path="${filter_dir}/${pcap_filename}"

        # Define the combined filter file path
        combined_filter_file="${filter_dir}/merged_${app_name}_combined_filter.txt"

        # Check if combined filter file exists
        if [[ -f "$combined_filter_file" ]]; then
            echo "Applying combined filter to create '$pcap_output_path'..."
            tshark -r "$MERGED_PCAP" -Y "$(cat "$combined_filter_file")" -w "$pcap_output_path"
            echo "Created PCAP: '$pcap_output_path'"
        else
            echo "Error: Combined filter file '$combined_filter_file' does not exist. Skipping."
        fi
    else
        echo "Warning: '$filter_dir' is not a directory. Skipping."
    fi
done

echo "==============================================="
echo "All filters have been applied. Outputs are located in the directory: $GLOBAL_OUTPUT_DIR"
echo "Script finished at $(date)"
echo "==============================================="