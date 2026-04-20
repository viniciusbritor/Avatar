#!/bin/bash
# Lana Watchdog - Auto Shutdown if idle for 30 minutes
IDLE_LIMIT=1800
RESULTS_DIR="/workspace/"
CHECK_FILE="/tmp/last_activity.txt"

# Ensure check file exists
if [ ! -f $CHECK_FILE ]; then
    touch $CHECK_FILE
fi

# 1. Check if any .mp4 files were updated in the last 30 mins
NEWEST_FILE=$(find $RESULTS_DIR -type f -name '*.mp4' -mmin -30 | wc -l)

# 2. Check if python3 inference is running
PYTHON_ACTIVE=$(pgrep -f "python3 -m scripts.inference" | wc -l)

if [ $NEWEST_FILE -gt 0 ] || [ $PYTHON_ACTIVE -gt 0 ]; then
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
