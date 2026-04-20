#!/bin/bash
# LANA INDUSTRIAL WATCHDOG V17
# Proteçao contra desligamento acidental durante bootstrap e inatividade.

IDLE_LIMIT=30 # Minutos de inatividade permitidos
LOCK_FILE="/tmp/lana_maestro.lock"
LOG_FILE="/workspace/watchdog_v17.log"

echo "$(date): Watchdog V17 Iniciado." >> $LOG_FILE

# Timer persistente em arquivo para sobreviver a pequenas quedas de script
STATE_FILE="/tmp/watchdog_idle_count"
if [ ! -f $STATE_FILE ]; then echo "0" > $STATE_FILE; fi

while true; do
    # 1. Verificar se o Maestro bloqueou o desligamento (Fase de Bootstrap/Deploy)
    if [ -f $LOCK_FILE ]; then
        echo "$(date): Maestro Lock Detectado. Resetando timer de inatividade." >> $LOG_FILE
        echo "0" > $STATE_FILE
    else
        # 2. Verificar se há processos de renderizaçao ou API ativos
        # Procuramos por: industrial_main.py ou inference.py
        if ps aux | grep -v grep | grep -E "industrial_main.py|inference.py" > /dev/null; then
            echo "$(date): Atividade detectada. Resetando timer." >> $LOG_FILE
            echo "0" > $STATE_FILE
        else
            # 3. Incrementar inatividade
            CURRENT_IDLE=$(cat $STATE_FILE)
            NEW_IDLE=$((CURRENT_IDLE + 1))
            echo $NEW_IDLE > $STATE_FILE
            echo "$(date): Inativo por $NEW_IDLE minutos." >> $LOG_FILE
            
            # 4. Desligamento Seguro
            if [ $NEW_IDLE -ge $IDLE_LIMIT ]; then
                echo "$(date): Limite de inatividade ($IDLE_LIMIT min) atingido. Desligando VM." >> $LOG_FILE
                sudo shutdown -h now
                exit 0
            fi
        fi
    fi
    sleep 60
done
