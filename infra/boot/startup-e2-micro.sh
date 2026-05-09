#!/bin/bash
# Lana API Startup — VM e2-micro (v4.4 — token direto, sem credential helper)
#   - Sem cron. Sem cache local. Sempre puxa do Artifact Registry.
#   - Boot: pull da ultima imagem. Se falhar → aborta. Sem fallback.
#   - Update: manual via "sudo lana-update.sh".
set -x
exec > /var/log/lana-startup.log 2>&1

echo "=== LANA API BOOT $(date) ==="

IMAGE="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest"

# 1. Docker
if ! command -v docker &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq docker.io
    systemctl start docker
    systemctl enable docker
fi

# 2. Auth Artifact Registry — token direto (sem credential helper)
#    Credential helper (docker-credential-gcloud) trava quando metadata server lento.
#    Token direto evita travar.
AUTH_OK=0
for i in $(seq 1 10); do
    if gcloud auth print-access-token | docker login -u oauth2accesstoken \
        --password-stdin us-east1-docker.pkg.dev 2>/dev/null; then
        AUTH_OK=1; break
    fi
    sleep 6
done
if [ "$AUTH_OK" = "0" ]; then
    echo "FATAL: Auth Artifact Registry falhou apos 10 tentativas."
    echo "Token direto como fallback..."
    gcloud auth print-access-token | docker login -u oauth2accesstoken \
        --password-stdin us-east1-docker.pkg.dev || { echo "Auth falhou. Abortando."; exit 1; }
fi

# 3. Instalar systemd unit ANTES do pull (idempotente)
#    Se o pull falhar, o unit ja existe. lana-update.sh consegue restart.
cat > /etc/systemd/system/lana-api.service << 'UNITEOF'
[Unit]
Description=Brasil AI — Avatar API (v3.2.4)
After=network.target docker.service
Requires=docker.service

[Service]
Type=exec
ExecStartPre=-/usr/bin/docker rm -f lana-api
ExecStart=/usr/bin/docker run --pull always \
    --name lana-api \
    --restart unless-stopped \
    --network host \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest
ExecStop=/usr/bin/docker stop -t 10 lana-api
Restart=on-failure
RestartSec=10
TimeoutStartSec=90
TimeoutStopSec=15
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
UNITEOF
systemctl daemon-reload
systemctl enable lana-api.service

# 4. Pull do Artifact Registry (fonte unica).
#    Se falhar → aborta boot (mas systemd unit ja instalado).
echo "Pulling $IMAGE..."
if ! timeout 120 docker pull "$IMAGE"; then
    echo "FATAL: Pull falhou no boot!"
    echo "O container NAO sera iniciado."
    echo "Execute 'sudo lana-update.sh' manualmente apos resolver."
    exit 1
fi
echo "Pull OK."
docker image prune -af 2>/dev/null || true

# 5. Iniciar container via systemd (ja instalado)
systemctl restart lana-api.service

# 6. Script de update manual (sem cron)
#    Uso: sudo /usr/local/bin/lana-update.sh
#    Puxa do Artifact Registry.
#    Se falhar → mantem container atual rodando (fallback seguro).
cat > /usr/local/bin/lana-update.sh << 'UPDATEEOF'
#!/bin/bash
set -e
IMAGE="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest"

echo "=== LANA UPDATE $(date) ==="
echo "Pulling $IMAGE ..."

if ! timeout 120 docker pull "$IMAGE"; then
    echo "FATAL: Pull da nova imagem falhou!"
    echo "Mantendo container atual rodando."
    echo "Verifique o Artifact Registry — imagem pode estar corrompida."
    exit 1
fi

echo "Pull OK. Restarting container..."
docker image prune -af 2>/dev/null || true
systemctl restart lana-api.service

# Verificar se a API subiu saudavel
echo "Verifying /health..."
sleep 10
if curl -sf --max-time 5 http://localhost:8080/health > /dev/null 2>&1; then
    echo "VERIFIED: API healthy on :8080"
else
    echo "WARNING: API nao respondeu no /health apos restart!"
    echo "Verifique os logs: sudo journalctl -u lana-api.service -f"
fi
echo "=== UPDATE DONE ==="
UPDATEEOF
chmod +x /usr/local/bin/lana-update.sh

# 7. Garantir que nao ha cron de polling
crontab -r 2>/dev/null || true

echo "=== BOOT COMPLETE ==="
