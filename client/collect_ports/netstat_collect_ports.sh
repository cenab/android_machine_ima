#!/bin/bash

while true; do
    timestamp=$(date +"%Y-%m-%d %T")
    adb shell netstat -p -n | grep com.Slack | sed "s/^/$timestamp /" >> netstat_output.txt
    sleep 60  # Adjust the interval as needed (in seconds)
done
