#!/bin/bash
# Lana Industrial Boot Script V18.11 (T4/L4 Multi-Arch Fix)

# 1. Detectar GPU
echo "[CHECK] Detectando arquitetura de GPU..."
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)

if [ ! -z "$1" ]; then
    echo "[GPU] Imagem especificada via argumento: $1"
    IMG_NAME="$1"
elif [[ $GPU_NAME == *"L4"* ]]; then
    echo "[GPU] NVIDIA L4 Detectada. Selecionando Imagem de Alta Performance (Ada Lovelace)."
    IMG_NAME="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0"
elif [[ $GPU_NAME == *"T4"* ]]; then
    echo "[GPU] NVIDIA T4 Detectada. Selecionando Imagem Gold de Resiliência."
    IMG_NAME="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-v6-t4-industrial-v1:latest"
else
    echo "[AVISO] GPU não identificada ($GPU_NAME). Usando imagem agnóstica de fallback."
    IMG_NAME="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-industrial:latest"
fi

echo "[CLEAN] Liberando espaço em disco..."
sudo docker system prune -f

echo "[PULL] Sincronizando imagem $IMG_NAME..."
if ! sudo docker pull $IMG_NAME; then
    echo "[ERRO] Falha ao puxar imagem. Verifique credenciais da Artifact Registry."
    exit 1
fi

# 2. Verificar Toolkit
if ! command -v nvidia-ctk &> /dev/null; then
    echo "[BOOT] Toolkit ausente. Instalando..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

# 3. Iniciar Motor Lana Industrial
echo "[BOOT] Iniciando Motor Lana Industrial..."
sudo docker stop lana-engine 2>/dev/null || true
sudo docker rm lana-engine 2>/dev/null || true

echo "[DOCKER] Iniciando container passivo (v2.7)..."
sudo docker run -d --name lana-engine --gpus all \
    --network host \
    -v /workspace:/workspace \
    -v /mnt/weights:/mnt/weights \
    $IMG_NAME \
    tail -f /dev/null

echo "[BOOT] Sistema pronto para orquestração Agno."

# 4. Iniciar Sentinela de Custos
echo "[FINOPS] Disparando Sentinela Zero-Waste..."
nohup bash /workspace/infra/lana-finops-sentinel.sh > /workspace/sentinel.log 2>&1 &

echo "[SUCESSO] Ambiente Industrial Ativo ($GPU_NAME)."
