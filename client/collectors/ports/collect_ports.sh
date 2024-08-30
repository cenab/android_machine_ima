#!/bin/bash

# Define an associative array with package names as keys and output filenames as values
declare -A apps
apps=(
    ["com.Slack"]="Slack_output.txt"
    ["com.Discord"]="Discord_output.txt"
    ["com.RocketChat"]="RocketChat_output.txt"
    ["com.Microsoft.Teams"]="Teams_output.txt"
    ["com.textnow"]="Textnow_output.txt"
    ["com.facebook.orca"]="Messenger_output.txt"
    ["org.telegram.messenger"]="Telegram_output.txt"
    ["org.thoughtcrime.securesms"]="Signal_output.txt"
    ["com.snapchat.android"]="Snapchat_output.txt"
    ["com.whatsapp"]="WhatsApp_output.txt"
)

while true; do
    timestamp=$(date +"%Y-%m-%d %T")
    for package in "${!apps[@]}"; do
        adb shell netstat -p -n | grep "$package" | sed "s/^/$timestamp /" >> "${apps[$package]}"
    done
    sleep 60  # Adjust the interval as needed (in seconds)
done
