#!/bin/bash
# Lana V17 - Zero Crash Resilience Setup
echo "--- INICIANDO BLINDAGEM DE INFRAESTRUTURA (v17) ---"

# 1. Criação de SWAP (20GB) para evitar OOM-Killer
if [ ! -f /swapfile_lana ]; then
    echo "[V17] Criando SWAP file de 20GB..."
    sudo fallocate -l 20G /swapfile_lana
    sudo chmod 600 /swapfile_lana
    sudo mkswap /swapfile_lana
    sudo swapon /swapfile_lana
    echo "/swapfile_lana none swap sw 0 0" | sudo tee -a /etc/fstab
    echo "[V17] SWAP Ativo."
else
    echo "[V17] SWAP já configurado."
fi

# 2. Otimização de Kernel (Swappiness)
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50

# 3. Heartbeat Watchdog V2 (Monitora o PID do Python)
cat << 'EOF' > /workspace/lana_watchdog_v2.sh
#!/bin/bash
# Watchdog Inteligente V2 - Proteção de Render
IDLE_LIMIT=5400 # 90 minutos de tolerância para debug
IDLE_TIME=0

echo "[WATCHDOG] Iniciando monitoramento resiliente..."

while true; do
    # Verifica se há renderização ativa (Inference ou HQ Restorer)
    IS_RENDERING=$(pgrep -f "inference.py" || pgrep -f "gfpgan")
    
    if [ -n "$IS_RENDERING" ]; then
        echo "[WATCHDOG] Render Ativo (PID $IS_RENDERING). Resetando idle timer."
        IDLE_TIME=0
    else
        IDLE_TIME=$((IDLE_TIME + 60))
        echo "[WATCHDOG] Sistema ocioso. Tempo acumulado: $IDLE_TIME / $IDLE_LIMIT segundos."
    fi

    if [ "$IDLE_TIME" -ge "$IDLE_LIMIT" ]; then
        echo "[WATCHDOG] Limite de inatividade atingido. Desligando motor..."
        sudo shutdown -h now
    fi
    
    sleep 60
done
EOF

sudo chmod +x /workspace/lana_watchdog_v2.sh
nohup /workspace/lana_watchdog_v2.sh > /workspace/watchdog_v2.log 2>&1 &

echo "--- INFRAESTRUTURA BLINDADA ---"
