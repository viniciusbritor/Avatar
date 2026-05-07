#!/bin/bash
# Lana API Startup — VM e2-micro (v4.1 — systemd + trigger GCS)
#   - Systemd unit lana-api.service (sobrevive a restart de VM e crash)
#   - Trigger-based update: verifica GCS a cada 1min. Só faz docker pull
#     quando o CI/CD escreve um trigger apos Cloud Build bem-sucedido.
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

# 4. Instalar systemd unit (idempotente)
cat > /etc/systemd/system/lana-api.service << 'UNITEOF'
[Unit]
Description=Brasil AI — Avatar API (v3.2.2)
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

# 5. Trigger-based update (CI/CD escreve trigger no GCS apos build)
cat > /usr/local/bin/lana-trigger-update.sh << 'TRIGEOF'
#!/bin/bash
TRIGGER="gs://brasil-ai-avatars-vault/triggers/lana-api-update.txt"
STATE_FILE="/var/lib/lana-api/last-trigger-ts"
IMAGE="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest"
mkdir -p /var/lib/lana-api

REMOTE_TS=$(gsutil cp "$TRIGGER" - 2>/dev/null | head -1 | tr -d '\n\r ')
[ -z "$REMOTE_TS" ] && exit 0

LOCAL_TS=$(cat "$STATE_FILE" 2>/dev/null)
if [ "$REMOTE_TS" != "$LOCAL_TS" ]; then
    echo "[TRIGGER-UPDATE] $(date): new trigger detected. Pulling..."
    docker pull "$IMAGE"
    docker image prune -f
    systemctl restart lana-api.service
    echo "$REMOTE_TS" > "$STATE_FILE"
fi
TRIGEOF
chmod +x /usr/local/bin/lana-trigger-update.sh
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/lana-trigger-update.sh") | crontab -

echo "=== BOOT COMPLETE ==="
