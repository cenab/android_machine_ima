#!/bin/bash

# Function to check ADB command success
check_adb_success() {
    local status=$1
    local output="$2"
    local message="$3"

    if [ $status -eq 0 ]; then
        echo "{\"status\": \"success\", \"message\": \"$message: Success\"}"
    else
        echo "{\"status\": \"failure\", \"message\": \"$message: Failed\", \"error\": \"$output\"}"
    fi
}

# Task queue
declare -a task_queue=()

# Function to add a task to the queue
add_task_to_queue() {
    task_queue+=("$1")
}

# Function to process the queue
process_queue() {
    local results=()
    for task in "${task_queue[@]}"; do
        echo "Processing task: $task"
        result=$(eval "$task")
        results+=("$result")
    done

    # Clear the queue after processing
    task_queue=()

    # Return all results as a JSON array
    echo "{\"results\": [$(IFS=,; echo "${results[*]}")]}"
}

# Function to automate Slack interactions
open_general_chat_from_home_screen() {
    local channel="$1"
    formatted_channel=${channel// /%s}  # Replaces spaces with %s
    formatted_channel=${formatted_channel//\'/\\\'}

    echo "Starting from home screen..."
    output=$(adb shell input keyevent KEYCODE_HOME 2>&1)
    result=$(check_adb_success $? "$output" "Return to Home Screen")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    # Wait for home screen to be ready
    wait_for_home_screen

    echo "Opening Slack..."
    output=$(adb shell am start -n com.Slack/slack.features.home.HomeActivity 2>&1)
    result=$(check_adb_success $? "$output" "Open Slack")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    # Wait for Slack to open
    wait_for_activity "slack.features.home.HomeActivity"

    echo "Opening DMs channel..."
    output=$(adb shell input tap 330 2180 2>&1)
    result=$(check_adb_success $? "$output" "Open DMs Channel")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    echo "Opening DMs search..."
    output=$(adb shell input tap 572 403 2>&1)
    result=$(check_adb_success $? "$output" "Open DMs Search")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    echo "Adding DM search input..."
    output=$(adb shell input text "'$formatted_channel'" 2>&1)
    result=$(check_adb_success $? "$output" "Add DM Search Input")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    echo "Opening general channel..."
    output=$(adb shell input tap 260 423 2>&1)
    result=$(check_adb_success $? "$output" "Open General Channel")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    echo "{\"status\": \"success\", \"message\": \"General chat opened successfully\"}"
}

# Function to post a message to the chat
post_message_to_the_chat() {
    # Check if the keyboard is shown
    check_keyboard

    local message="${1// /%s}"  # Replaces all spaces with '%s'
    formatted_message="${message//\'/\'\\\'\'}"

    # Clicks on the text box
    output=$(adb shell input tap 550 2200 2>&1)
    result=$(check_adb_success $? "$output" "Click Text Box")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    # Writes your text
    output=$(adb shell input text "'$formatted_message'" 2>&1)
    result=$(check_adb_success $? "$output" "Write Text")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    # Clicks on send button
    output=$(adb shell input tap 1000 1450 2>&1)
    result=$(check_adb_success $? "$output" "Click Send Button")
    [ $(echo "$result" | jq -r .status) == "failure" ] && echo "$result" && return

    echo "{\"status\": \"success\", \"message\": \"Message posted successfully\"}"
}

# Function to return to the home screen
return_to_home_screen() {
    # Returns to home screen
    output=$(adb shell input keyevent KEYCODE_HOME 2>&1)
    check_adb_success $? "$output" "Return to Home Screen"
}

# Function to wait for the home screen
wait_for_home_screen() {
    echo "Waiting for home screen..."
    until adb shell dumpsys window | grep -m 1 'mCurrentFocus=Window{.*StatusBar};'; do
        sleep 0.5
    done
    echo "{\"status\": \"success\", \"message\": \"Home screen is ready\"}"
}

# Function to wait for a specific activity
wait_for_activity() {
    local activity="$1"
    echo "Waiting for $activity to start..."
    until adb shell dumpsys window | grep -m 1 "mCurrentFocus=Window{.*$activity}"; do
        sleep 0.5
    done
    echo "{\"status\": \"success\", \"message\": \"$activity is ready\"}"
}

# Function to check if the keyboard is shown
check_keyboard() {
    KEYBOARD_STATUS=$(adb shell dumpsys input_method | grep "mInputShown" | awk '{print $NF}')

    if [ "$KEYBOARD_STATUS" = "true" ]; then
        adb shell input keyevent KEYCODE_BACK
        echo "{\"status\": \"success\", \"message\": \"Keyboard hidden\"}"
    else
        echo "{\"status\": \"success\", \"message\": \"Keyboard is not shown\"}"
    fi
}

# Process the queued tasks
process_queue