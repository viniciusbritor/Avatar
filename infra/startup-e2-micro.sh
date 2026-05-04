#!/bin/bash
# Lana API Startup — VM e2-micro (v3 — auto-cura)
# Features:
#   - Cron auto-update: docker pull a cada 5min
#   - Health check: se API cair 3x, restart container
#   - Idempotente: roda seguro no boot e manualmente
set -x
exec > /var/log/lana-startup.log 2>&1

echo "=== LANA API BOOT $(date) ==="

# 1. Docker
if ! command -v docker &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq docker.io
    systemctl start docker
    systemctl enable docker
fi

# 2. Auth Artifact Registry — com retry
for i in $(seq 1 10); do
    gcloud auth configure-docker us-east1-docker.pkg.dev --quiet && break
    sleep 6
done

# 3. Pull com retry
for i in $(seq 1 5); do
    echo "PULL attempt $i..."
    docker pull us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest && break
    sleep 10
done

# 3. Run
docker rm -f lana-api 2>/dev/null
docker run -d --name lana-api \
    --restart unless-stopped \
    --network host \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest

# 4. Auto-update via cron (a cada 5min verifica imagem nova)
cat > /usr/local/bin/lana-auto-update.sh << 'CRONEOF'
#!/bin/bash
IMAGE="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest"
BEFORE=$(docker inspect --format='{{.Id}}' $IMAGE 2>/dev/null || echo "")
docker pull $IMAGE --quiet 2>/dev/null
AFTER=$(docker inspect --format='{{.Id}}' $IMAGE 2>/dev/null || echo "")
if [ -n "$BEFORE" ] && [ -n "$AFTER" ] && [ "$BEFORE" != "$AFTER" ]; then
    echo "[AUTO-UPDATE] Nova imagem detectada. Reiniciando..."
    docker rm -f lana-api
    docker run -d --name lana-api --restart unless-stopped --network host $IMAGE
fi
CRONEOF
chmod +x /usr/local/bin/lana-auto-update.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/lana-auto-update.sh") | crontab -

# 5. Health check auto-restart (a cada 1min)
cat > /usr/local/bin/lana-health-check.sh << 'HEALEOF'
#!/bin/bash
FAILS=0
for i in $(seq 1 3); do
    if curl -s --connect-timeout 3 http://localhost:8080/health > /dev/null 2>&1; then
        exit 0
    fi
    FAILS=$((FAILS+1))
    sleep 5
done
echo "[HEALTH-CHECK] API falhou $FAILS vezes. Reiniciando container..."
docker restart lana-api
HEALEOF
chmod +x /usr/local/bin/lana-health-check.sh
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/lana-health-check.sh") | crontab -

echo "=== BOOT COMPLETE ==="
