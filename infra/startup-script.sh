#!/bin/bash
# Lana Industrial Engine v14.0 - Startup Script Soberano
# Objetivo: Automação Stateless, Persistência Global & Gestão de Inatividade

echo "[LANA] Iniciando provisionamento industrial (v14.0)..."

# 1. Configurar volumes Docker
mkdir -p /app/checkpoints
mkdir -p /app/outputs

# 2. Sincronizar Modelos (Backbone GCS)
echo "[LANA] Sincronizando pesos (15GB) do GCS..."
gsutil -m cp -r gs://brasil-ia-lana-assets/models/* /app/checkpoints/

# 3. Inicializar Motor Docker
echo "[LANA] Subindo container Docker..."
docker stop lana-engine || true
docker rm lana-engine || true
docker run -d --name lana-engine --gpus all \
  -p 8080:8080 \
  -v /app/checkpoints:/app/checkpoints \
  -v /app/outputs:/app/outputs \
  -e GCS_BUCKET=brasil-ai-avatars \
  lana-engine-industrial:latest

# 4. Sentinela de Inatividade (Gestão de Custos)
echo "[LANA] Configurando Sentinela de Inatividade..."
cat << 'EOF' > /usr/local/bin/sentinel.sh
#!/bin/bash
# Lana Sentinel v15.0 - Heartbeat Aware
UPTIME=$(cat /proc/uptime | cut -f1 -d.)
HEARTBEAT_FILE="/workspace/heartbeat"

# 1. Verificar se houve pulso de vida (Heartbeat) recente
if [ -f "$HEARTBEAT_FILE" ]; then
  echo "[SENTINEL] Heartbeat detectado. Mantendo máquina aquecida."
  rm "$HEARTBEAT_FILE"
  exit 0
fi

# 2. Se não houver heartbeat, auditar ociosidade após 25 min de boot
if [ ${UPTIME%.*} -gt 1500 ]; then
  # Verifica utilidade da GPU. Se menor que 5%, assume ociosidade.
  GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -n 1)
  if [ "$GPU_UTIL" -lt 5 ]; then
    echo "[SENTINEL] Ociosidade detectada ($GPU_UTIL%). Desligando para economia."
    sudo shutdown -h now
  fi
fi
EOF
chmod +x /usr/local/bin/sentinel.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /bin/bash /usr/local/bin/sentinel.sh") | crontab -

echo "[LANA] Motor pronto. Monitoramento de custos ATIVO (sentinel.sh)."
