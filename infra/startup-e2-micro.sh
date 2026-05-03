#!/bin/bash
# Lana API Startup — VM e2-micro (v2 — robusto)
set -x
exec > /var/log/lana-startup.log 2>&1

echo "=== LANA API BOOT $(date) ==="

# 1. Docker
if ! command -v docker &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq docker.io
    systemctl start docker
    systemctl enable docker
fi

# 2. Auth
gcloud auth configure-docker us-east1-docker.pkg.dev --quiet

# 3. Pull com retry
for i in $(seq 1 5); do
    echo "PULL attempt $i..."
    docker pull us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest && break
    sleep 10
done

# 4. Run
docker rm -f lana-api 2>/dev/null
docker run -d --name lana-api \
    --restart unless-stopped \
    --network host \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest

echo "=== BOOT COMPLETE ==="
