#!/bin/bash
# Lana API Startup — VM e2-micro (v4 — systemd)
# Features:
#   - Systemd unit lana-api.service (sobrevive a restart de VM e crash)
#   - Cron auto-update: docker pull a cada 5min → systemctl restart
#   - Health check: se API cair 3x → systemctl restart
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

# 4. Instalar systemd unit (idempotente — roda na VM host, NÃO no container)
cat > /etc/systemd/system/lana-api.service << 'UNITEOF'
[Unit]
Description=Brasil AI — Avatar API (v3.2.1)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
ExecStartPre=-/usr/bin/docker rm -f lana-api
ExecStart=/usr/bin/docker run --name lana-api \
    --restart=no \
    --network host \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest
ExecStop=/usr/bin/docker stop lana-api
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF
systemctl daemon-reload
systemctl enable lana-api.service
systemctl restart lana-api.service

# 5. Auto-update via cron (a cada 5min verifica imagem nova)
cat > /usr/local/bin/lana-auto-update.sh << 'CRONEOF'
#!/bin/bash
IMAGE="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest"
BEFORE=$(docker inspect --format='{{.Id}}' $IMAGE 2>/dev/null || echo "")
docker pull $IMAGE --quiet 2>/dev/null
AFTER=$(docker inspect --format='{{.Id}}' $IMAGE 2>/dev/null || echo "")
if [ -n "$BEFORE" ] && [ -n "$AFTER" ] && [ "$BEFORE" != "$AFTER" ]; then
    echo "[AUTO-UPDATE] Nova imagem detectada. Reiniciando..."
    systemctl restart lana-api.service
fi
CRONEOF
chmod +x /usr/local/bin/lana-auto-update.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/lana-auto-update.sh") | crontab -

# 6. Health check auto-restart (a cada 1min)
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
echo "[HEALTH-CHECK] API falhou $FAILS vezes. Reiniciando..."
systemctl restart lana-api.service
HEALEOF
chmod +x /usr/local/bin/lana-health-check.sh
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/lana-health-check.sh") | crontab -

echo "=== BOOT COMPLETE ==="
