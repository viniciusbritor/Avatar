#!/bin/bash
# Lana Industrial Startup Script - Architecture 4 (Stateless + GCS Fuse)
# v5 — Sistema anti-desperdício: Sentinel roda no HOST, não no container.
# Se o container morrer, o Sentinel na VM desliga em 30 min.

echo "--- INICIANDO BOOT INDUSTRIAL ARCH 4 ---"

# 1. DEAD MAN'S SWITCH (90 min — safety net absoluta)
echo "sudo shutdown -P +90" | at now 2>/dev/null || (apt-get update -qq && apt-get install -y -qq at && echo "sudo shutdown -P +90" | at now)

# 2. INSTALAR DOCKER E NVIDIA TOOLKIT
if ! command -v docker &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq docker.io
    systemctl start docker
    systemctl enable docker
fi

if ! command -v nvidia-ctk &> /dev/null; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update -qq && apt-get install -y -qq nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# 3. INSTALAR GCS FUSE
if ! command -v gcsfuse &> /dev/null; then
    export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
    echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
    apt-get update -qq
    apt-get install -y -qq gcsfuse
fi

# 4. MONTAR BUCKET DE PESOS
mkdir -p /mnt/weights
chmod 777 /mnt/weights
gcsfuse -o allow_other --only-dir checkpoints lana-weights-universal /mnt/weights

# 5. PREPARAR WORKSPACE
mkdir -p /workspace
chmod 777 /workspace

# 6. CONFIGURAR DOCKER AUTH
for i in $(seq 1 10); do
    gcloud auth configure-docker us-east1-docker.pkg.dev --quiet && break
    sleep 6
done

# 7. PULL GOLDEN IMAGE L4
echo "--- PULL IMAGEM L4 GOLDEN ---"
for i in $(seq 1 5); do
    echo "PULL attempt $i..."
    docker pull us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10-golden && break
    sleep 15
done

# 8. SYNC ASSETS
echo "--- SYNC ASSETS ---"
mkdir -p /workspace/latentsync/assets
gsutil -m cp gs://lana-weights-universal/assets/*.mp4 /workspace/latentsync/assets/ 2>/dev/null || true
rm -rf /workspace/latentsync/checkpoints
ln -sfn /mnt/weights /workspace/latentsync/checkpoints
chmod -R 777 /workspace

# 9. COPIAR CÓDIGO PYTHON DA IMAGEM PARA O HOST
#    A imagem golden tem os scripts em /workspace/src/,
#    mas o mount -v /workspace:/workspace esconde eles.
#    Extraímos para /workspace/src/ no host antes de rodar.
echo "--- EXTRAINDO CODIGO PYTHON DA IMAGEM ---"
TEMP_CONTAINER=$(docker create us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10-golden)
docker cp "$TEMP_CONTAINER:/workspace/src" /workspace/src
docker cp "$TEMP_CONTAINER:/workspace/latentsync" /workspace/latentsync
docker rm "$TEMP_CONTAINER"
chmod -R 777 /workspace/src
chmod -R 777 /workspace/latentsync

# 10. RUN CONTAINER
echo "--- INICIANDO CONTAINER L4 ---"
API_KEY=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/api-key 2>/dev/null || echo "brasilai-avatar-2026")
docker rm -f lana-engine 2>/dev/null
docker run -d --name lana-engine \
    --gpus all \
    --network host \
    --restart=no \
    -e API_SECRET_KEY="$API_KEY" \
    -v /workspace:/workspace \
    -v /mnt/weights:/mnt/weights \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10-golden \
    python3 /workspace/src/industrial_main.py

# 11. SENTINEL NO HOST (systemd — roda FORA do container)
#    Se o container morrer → shutdown em MAX_DEAD_CYCLES
#    Se a GPU ficar idle → shutdown em MAX_IDLE_CYCLES
cat <<'SENTINEL_EOF' > /usr/local/bin/lana-host-sentinel.sh
#!/bin/bash
STATUS_FILE="/workspace/sentinel_status.json"
IDLE_CYCLES=0
DEAD_CYCLES=0
MAX_IDLE=60           # 30 min (30s * 60)
MAX_DEAD=60           # 30 min (30s * 60) — container morreu
BOOT_GRACE=600        # 10 min de graça no boot

echo "[SENTINEL-HOST] Iniciado. Monitorando container lana-engine + GPU..."

sleep 60  # Espera 1 min pelo container estabilizar

while true; do
    UPTIME_SEC=$(cat /proc/uptime | awk '{print $1}' | cut -d. -f1)
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -n 1)
    [ -z "$GPU_UTIL" ] && GPU_UTIL=0
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n 1)

    CONTAINER_ALIVE=$(docker ps --filter name=lana-engine --format '{{.Names}}' 2>/dev/null)

    if [ -n "$CONTAINER_ALIVE" ]; then
        DEAD_CYCLES=0
        # Container vivo: usa lógica de GPU + heartbeat
        if [ "$GPU_UTIL" -gt 5 ] || [ -f "/workspace/heartbeat" ]; then
            IDLE_CYCLES=0
            STATE="ACTIVE"
            rm -f /workspace/heartbeat
        else
            IDLE_CYCLES=$((IDLE_CYCLES+1))
            STATE="IDLE"
        fi
    else
        # Container MORTO: contagem regressiva acelerada
        DEAD_CYCLES=$((DEAD_CYCLES+1))
        STATE="CONTAINER_DEAD"
        echo "[SENTINEL-HOST] ALERTA: Container lana-engine nao esta rodando! Ciclo $DEAD_CYCLES/$MAX_DEAD"
    fi

    REMAINING_CYCLES=$((MAX_IDLE - IDLE_CYCLES))
    REMAINING_MIN=$((REMAINING_CYCLES / 2))

    cat <<JSON_EOF > $STATUS_FILE
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "gpu_name": "$GPU_NAME",
  "gpu_utilization": $GPU_UTIL,
  "state": "$STATE",
  "idle_cycles": $IDLE_CYCLES,
  "max_idle": $MAX_IDLE,
  "dead_cycles": $DEAD_CYCLES,
  "max_dead": $MAX_DEAD,
  "uptime_seconds": $UPTIME_SEC,
  "remaining_minutes": $REMAINING_MIN,
  "container_alive": $( [ -n "$CONTAINER_ALIVE" ] && echo "true" || echo "false" )
}
JSON_EOF

    # Shutdown por container morto
    if [ "$DEAD_CYCLES" -ge "$MAX_DEAD" ] && [ "$UPTIME_SEC" -gt "$BOOT_GRACE" ]; then
        echo "[SHUTDOWN] Container lana-engine morto por ${DEAD_CYCLES} ciclos. Desligando para Custo Zero."
        sudo poweroff
    fi

    # Shutdown por inatividade
    if [ "$IDLE_CYCLES" -ge "$MAX_IDLE" ] && [ "$UPTIME_SEC" -gt "$BOOT_GRACE" ]; then
        echo "[SHUTDOWN] GPU ociosa por ${IDLE_CYCLES} ciclos. Desligando para Custo Zero."
        sudo poweroff
    fi

    sleep 30
done
SENTINEL_EOF

chmod +x /usr/local/bin/lana-host-sentinel.sh

# Instalar como systemd service
cat <<'UNIT_EOF' > /etc/systemd/system/lana-sentinel.service
[Unit]
Description=Lana Host-Level Sentinel — Zero-Waste Shutdown
After=docker.service network.target
Wants=docker.service

[Service]
Type=simple
ExecStart=/usr/local/bin/lana-host-sentinel.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT_EOF

systemctl daemon-reload
systemctl enable lana-sentinel.service
systemctl start lana-sentinel.service

echo "--- BOOT FINALIZADO: GPU PRONTA + SENTINEL HOST ATIVO ---"
