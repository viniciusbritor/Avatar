#!/bin/bash
# Lana Enterprise Watchdog - Módulo Zero-Desperdício (30s)
# Logs status for the "Barra de Status" Dashboard.

STATUS_FILE="/workspace/sentinel_status.json"
IDLE_CYCLES=0
MAX_IDLE=60 # 30 minutes (30s * 60)

echo "[SENTINEL] Iniciando monitoramento industrial..."

while true; do
    # 1. Medir métricas
    UPTIME_SEC=$(cat /proc/uptime | awk '{print $1}' | cut -d. -f1)
    GPU_UTIL=$(sudo nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -n 1)
    GPU_NAME=$(sudo nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    
    if [ -z "$GPU_UTIL" ]; then GPU_UTIL=0; fi

    # 2. Lógica de Ócio (GPU ou Heartbeat Manual)
    if [ "$GPU_UTIL" -gt 5 ] || [ -f "/workspace/heartbeat" ]; then
        IDLE_CYCLES=0
        STATE="ACTIVE"
        # Consome o heartbeat
        sudo rm -f /workspace/heartbeat
    else
        IDLE_CYCLES=$((IDLE_CYCLES+1))
        STATE="IDLE"
    fi

    # 3. Gerar JSON de Status para a Barra
    REMAINING_CYCLES=$((MAX_IDLE - IDLE_CYCLES))
    REMAINING_MIN=$((REMAINING_CYCLES / 2))
    
    cat <<EOF > $STATUS_FILE
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "gpu_name": "$GPU_NAME",
  "gpu_utilization": $GPU_UTIL,
  "state": "$STATE",
  "idle_cycles": $IDLE_CYCLES,
  "max_idle": $MAX_IDLE,
  "uptime_seconds": $UPTIME_SEC,
  "remaining_minutes": $REMAINING_MIN
}
EOF

    # 4. Decisão de Shutdown
    if [ "$IDLE_CYCLES" -ge "$MAX_IDLE" ]; then
        if [ "$UPTIME_SEC" -gt 600 ]; then # Proteção de boot (10 min)
            echo "[SHUTDOWN] Sentinela detectou ociosidade plena. Desligando para Custo Zero."
            sudo poweroff
        fi
    fi

    sleep 30
done
