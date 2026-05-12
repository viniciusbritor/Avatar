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
fi
# Garante runtime configurado mesmo se já instalado (sobrevive a restart)
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
# Garante runtime configurado mesmo se já instalado (sobrevive a restart)
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

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

# 7. PULL L4 IMAGE (deps apenas, código Python vem do git clone)
echo "--- PULL IMAGEM L4 v2.10 (deps) ---"
for i in $(seq 1 5); do
    echo "PULL attempt $i..."
    docker pull us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10 && break
    sleep 15
done

# 8. GIT CLONE — código fresco do GitHub (NUNCA docker cp)
#    ARCHITECTURE.md: "Código Python obtido fresco do GitHub no boot"
echo "--- GIT CLONE REPO + SUBMODULES ---"
if [ -d /workspace/.git ]; then
    git -C /workspace pull --recurse-submodules || true
    git -C /workspace submodule update --init --recursive
else
    git clone --recurse-submodules https://github.com/viniciusbritor/Avatar.git /workspace/ || {
        echo "FATAL: git clone falhou. Abortando boot."
        exit 1
    }
fi

# 9. OVERRIDES CRÍTICOS (patches que estavam na golden image)
#    V30 contrast fix + GFPGAN photorealism + progress tracking
echo "--- APLICANDO OVERRIDES (V30 + Progress Tracking) ---"
cp /workspace/infra/docker/lipsync_pipeline_v30.py /workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py
cp /workspace/infra/docker/inference.py /workspace/latentsync/scripts/inference.py

# 10. SYNC ASSETS + CHECKPOINTS (após git clone, sem conflito)
echo "--- SYNC ASSETS ---"
mkdir -p /workspace/latentsync/assets
gsutil -m cp gs://lana-weights-universal/assets/*.mp4 /workspace/latentsync/assets/ 2>/dev/null || true
rm -rf /workspace/latentsync/checkpoints
ln -sfn /mnt/weights /workspace/latentsync/checkpoints
chmod -R 777 /workspace

# 11. RUN CONTAINER (com auto-recovery CUDA)
echo "--- INICIANDO CONTAINER L4 ---"
docker rm -f lana-engine 2>/dev/null
docker run -d --name lana-engine \
    --gpus all \
    --network host \
    --restart=no \
    -e API_SECRET_KEY="brasilai-avatar-2026" \
    -v /workspace:/workspace \
    -v /mnt/weights:/mnt/weights \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10 \
    python3 /workspace/src/industrial_main.py

# Auto-recovery: se CUDA falhar (Docker acabou de reiniciar, runtime NVIDIA
# ainda nao estabilizou), recria o container — igual stop+rm+run manual.
sleep 15
if ! docker exec lana-engine python3 -c "import torch; print('CUDA:', torch.cuda.is_available()); assert torch.cuda.is_available()" 2>&1 | tee /tmp/cuda_check.log; then
    echo "[BOOT] CUDA falhou no primeiro start ($(cat /tmp/cuda_check.log)), recriando container..."
    docker rm -f lana-engine
    sleep 3
    docker run -d --name lana-engine \
        --gpus all \
        --network host \
        --restart=no \
        -e API_SECRET_KEY="brasilai-avatar-2026" \
        -v /workspace:/workspace \
        -v /mnt/weights:/mnt/weights \
        us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10 \
        python3 /workspace/src/industrial_main.py
    echo "[BOOT] Container recriado apos recovery CUDA."
else
    echo "[BOOT] CUDA OK no primeiro start."
fi

# 12. SENTINEL NO HOST (systemd — roda FORA do container)
#    Se o container morrer → delete instância em MAX_DEAD_CYCLES
#    Se a GPU ficar idle → delete instância em MAX_IDLE_CYCLES
#    Sinal shutdown_now (do container) → delete imediato
cat <<'SENTINEL_EOF' > /usr/local/bin/lana-host-sentinel.sh
#!/bin/bash
STATUS_FILE="/workspace/sentinel_status.json"
IDLE_CYCLES=0
DEAD_CYCLES=0
MAX_IDLE=60           # 30 min (30s * 60)
MAX_DEAD=60           # 30 min (30s * 60) — container morreu
BOOT_GRACE=600        # 10 min de graça no boot

# --- Delete instance + disk (Zero-Waste). Fallback: poweroff se falhar. ---
delete_instance() {
    local NAME ZONE PROJECT
    PROJECT="brasili-ia-news"
    NAME=$(curl -sf -H "Metadata-Flavor: Google" \
        http://metadata.google.internal/computeMetadata/v1/instance/name 2>/dev/null)
    ZONE=$(curl -sf -H "Metadata-Flavor: Google" \
        http://metadata.google.internal/computeMetadata/v1/instance/zone 2>/dev/null | awk -F/ '{print $NF}')

    if [ -n "$NAME" ] && [ -n "$ZONE" ]; then
        echo "[SHUTDOWN] Deletando instancia $NAME ($ZONE) com disco..."
        if gcloud compute instances delete "$NAME" \
            --zone="$ZONE" \
            --project="$PROJECT" \
            --delete-disks=all \
            --quiet 2>/dev/null; then
            echo "[SHUTDOWN] Instancia + disco deletados. Custo Zero."
            return 0
        fi
        echo "[SHUTDOWN] gcloud delete falhou. Fallback para poweroff."
    else
        echo "[SHUTDOWN] Metadata indisponivel (NAME='$NAME' ZONE='$ZONE'). Fallback para poweroff."
    fi
    sudo poweroff
}

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
        # Sinal de shutdown imediato vindo do container (job concluído ou idle)
        if [ -f "/workspace/shutdown_now" ]; then
            echo "[SHUTDOWN] Sinal shutdown_now recebido. Deletando instancia imediatamente."
            delete_instance
        fi
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
        echo "[SHUTDOWN] Container lana-engine morto por ${DEAD_CYCLES} ciclos."
        delete_instance
    fi

    # Shutdown por inatividade
    if [ "$IDLE_CYCLES" -ge "$MAX_IDLE" ] && [ "$UPTIME_SEC" -gt "$BOOT_GRACE" ]; then
        echo "[SHUTDOWN] GPU ociosa por ${IDLE_CYCLES} ciclos."
        delete_instance
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
