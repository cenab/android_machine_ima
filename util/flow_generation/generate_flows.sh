#!/bin/bash

# Find the full path to tranalyzer
TRANALYZER_PATH=$(which tranalyzer)

if [ -z "$TRANALYZER_PATH" ]; then
    echo "Error: tranalyzer not found in PATH"
    exit 1
fi

# Function to process a single PCAP file
process_pcap() {
    input_pcap="$1"
    output_dir="$(dirname "$input_pcap")"
    echo "Processing $input_pcap"
    "$TRANALYZER_PATH" -r "$input_pcap" -w "$output_dir"
    if [ $? -eq 0 ]; then
        echo "Successfully processed $input_pcap"
    else
        echo "Error processing $input_pcap"
    fi
}

# Function to recursively process PCAP files in a directory
process_directory() {
    local dir="$1"
    for file in "$dir"/*_filtered.pcap; do
        if [ -f "$file" ]; then
            process_pcap "$file"
        fi
    done
    for subdir in "$dir"/*/ ; do
        if [ -d "$subdir" ]; then
            process_directory "$subdir"
        fi
    done
}

# Main execution
root_directory="${1:-.}"  # Use first argument if provided, otherwise use current directory
process_directory "$root_directory"

echo "All PCAP files processed."