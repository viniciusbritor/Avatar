#!/bin/bash
# Lana Enterprise Watchdog - Módulo Zero-Desperdício (30s)
# Este script avalia o uso de processamento e conexões a cada 15s.

IDLE_CYCLES=0

while true; do
    sleep 30
    
    # Proteção de carência de Boot (Ignora primeiros 3 minutos de vida da máquina)
    UPTIME_SEC=$(cat /proc/uptime | awk '{print $1}' | cut -d. -f1)
    if [ "$UPTIME_SEC" -lt 180 ]; then
        continue
    fi

    # Mede uso de GPU (Qualquer pico zera a ociosidade)
    GPU_USAGE=$(sudo nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -n 1)
    
    if [ -z "$GPU_USAGE" ]; then GPU_USAGE=0; fi

    # Se a GPU estiver trabalhando (>5% de uso), a máquina está viva
    if [ "$GPU_USAGE" -gt 2 ]; then
        IDLE_CYCLES=0
    else
        # Se não há uso de GPU, incrementar contador de ócio
        IDLE_CYCLES=$((IDLE_CYCLES+1))
    fi

    # Se acumulou 60 ciclos seguidos (30 segundos * 60 = 1800 segundos = 30 minutos)
    if [ "$IDLE_CYCLES" -ge 60 ]; then
        echo "Sentinela detectou 30 minutos de Ociosidade Plena da GPU. Executando Custo Zero: Hibernando."
        sudo poweroff
    fi
done
