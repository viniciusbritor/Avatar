#!/bin/bash
# Lana Industrial Boot Script V19-BAKED (Zero Cold Start + Self-Healing + Auto-Patch)
# Objetivo: Ligar o motor em menos de 5 segundos com integridade total.

echo "[V19] Iniciando Ignição Relâmpago (Pre-Baked Mode)..."

# 1. Identificar a imagem (Prioridade para o argumento do Orquestrador)
IMG_NAME=${1:-"us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.8"}
echo "[V19] Usando Imagem: $IMG_NAME"

# 2. Restaurar código se necessário
if [ ! -d "/workspace/latentsync" ]; then
    echo "[V19] Código do LatentSync ausente. Restaurando via Git..."
    sudo git clone https://github.com/bytedance/LatentSync /workspace/latentsync
    sudo chmod -R 777 /workspace/latentsync
fi

# Sincronizar Assets do Bucket (Apenas se necessário)
if [ -z "$(ls -A /workspace/latentsync/assets/ 2>/dev/null)" ]; then
    echo "[V19] Sincronizando Assets do Bucket..."
    sudo mkdir -p /workspace/latentsync/assets/
    sudo gsutil -m cp gs://lana-weights-universal/assets/*.mp4 /workspace/latentsync/assets/
else
    echo "[V19] Assets já presentes. Pulando download."
fi

# Criar Ponte de Modelos (Checkpoints via GCS Fuse)
echo "[V19] Mapeando Checkpoints Industriais..."
sudo rm -rf /workspace/latentsync/checkpoints
sudo ln -sfn /mnt/weights /workspace/latentsync/checkpoints
sudo mkdir -p /workspace/latentsync/checkpoints/gfpgan
sudo ln -sfn /mnt/weights/gfpgan/GFPGANv1.4.pth /workspace/latentsync/checkpoints/gfpgan/GFPGANv1.4.pth
sudo chmod -R 777 /workspace/latentsync/checkpoints

# 3. Aplicar Patches Industriais (Movendo arquivos do orquestrador para o lugar certo)
echo "[V19] Aplicando Patches de Produção..."
sudo cp /workspace/industrial_main.py /workspace/latentsync/industrial_main.py
sudo mkdir -p /workspace/latentsync/latentsync/pipelines/
sudo cp /workspace/lipsync_pipeline.py /workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py

# Garantir que a autenticação do Artifact Registry esteja pronta antes do Pull
echo "[V19] Autenticando Docker no GCP Artifact Registry..."
sudo gcloud auth configure-docker us-east1-docker.pkg.dev -q

# 4. Limpeza Instantânea
sudo docker stop lana-engine 2>/dev/null || true
sudo docker rm lana-engine 2>/dev/null || true

# 5. Iniciar Motor com Verificação de Dependências Críticas
echo "[V19] Disparando Motor Lana Industrial..."
sudo docker run -d --name lana-engine --gpus all \
    --network host \
    -v /workspace:/workspace \
    -v /mnt/weights:/mnt/weights \
    $IMG_NAME \
    tail -f /dev/null

# 6. Iniciar Sentinela de Custos
echo "[FINOPS] Disparando Sentinela Zero-Waste..."
nohup bash /workspace/infra/lana-finops-sentinel.sh > /workspace/sentinel.log 2>&1 &

echo "[SUCESSO] Motor V19 Ativo em modo Ultra-Fast e Patched."
