#!/bin/bash
sudo docker stop $(sudo docker ps -q) 2>/dev/null
sudo docker run -d --name lana_engine --rm --gpus all -p 8080:8080 -v /workspace:/workspace us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-universal:v2.0 bash -c "cd /workspace/latentsync && python industrial_main.py"

# Triggers FinOps Auto-Hibernation Watchdog in the background
sudo bash /workspace/lana-finops-sentinel.sh &
