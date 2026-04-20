#!/bin/bash
# Sentinela de Inatividade Inteligente v2.0
# Desliga a VM se a GPU estiver ociosa e NÃO houver renderização ativa.

THRESHOLD=5
MINUTES_IDLE=30
LOCK_FILE="/tmp/lana_industrial.lock"

# Verifica se o processo de renderização está em andamento (Lock File)
if [ -f "$LOCK_FILE" ]; then
    echo "$(date): Renderização ativa detectada ($LOCK_FILE). Sentinela em stand-by." >> /var/log/sentinel.log
    exit 0
fi

# Verifica carga da GPU via nvidia-smi
GPU_LOAD=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{sum+=$1} END {print sum}')

if [ "$GPU_LOAD" -lt "$THRESHOLD" ]; then
    # Incrementa contador de ociosidade
    IDLE_COUNT=$(cat /tmp/gpu_idle_count 2>/dev/null || echo 0)
    IDLE_COUNT=$((IDLE_COUNT + 1))
    echo $IDLE_COUNT > /tmp/gpu_idle_count
    
    echo "$(date): GPU ociosa ($GPU_LOAD%). Ciclo $IDLE_COUNT/$MINUTES_IDLE" >> /var/log/sentinel.log
    
    if [ "$IDLE_COUNT" -ge "$MINUTES_IDLE" ]; then
        echo "$(date): Inatividade confirmada. Disparando Zero-Waste Shutdown." >> /var/log/sentinel.log
        rm /tmp/gpu_idle_count
        sudo shutdown -h now
    fi
else
    echo 0 > /tmp/gpu_idle_count
    echo "$(date): GPU ativa ($GPU_LOAD%). Resetando sentinela." >> /var/log/sentinel.log
fi
