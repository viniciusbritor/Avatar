#!/bin/bash
# Lana Watchdog - Auto Shutdown if idle for 30 minutes
IDLE_LIMIT=1800
RESULTS_DIR="/mnt/disks/data/results/"
CHECK_FILE="/tmp/last_activity.txt"

# Ensure check file exists
if [ ! -f $CHECK_FILE ]; then
    touch $CHECK_FILE
fi

# Check if any .mp4 files were created in the last 30 mins
NEWEST_FILE=$(find $RESULTS_DIR -type f -name '*.mp4' -mmin -30 | wc -l)

if [ $NEWEST_FILE -gt 0 ]; then
    # Active! Update check file
    touch $CHECK_FILE
fi

LAST_ACTIVITY=$(stat -c %Y $CHECK_FILE)
NOW=$(date +%s)
IDLE_TIME=$((NOW - LAST_ACTIVITY))

if [ $IDLE_TIME -gt $IDLE_LIMIT ]; then
    echo "[WATCHDOG] Lana Engine idle for $IDLE_TIME seconds. Shutting down to save costs..."
    sudo shutdown -h now
else
    echo "[WATCHDOG] Lana Engine active. Idle time: $IDLE_TIME seconds."
fi
