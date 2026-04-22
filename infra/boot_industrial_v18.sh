#!/bin/bash
# Lana Industrial Boot Script V18.10 (No-Context Build Fix)
IMG_NAME="us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0"

echo "[CLEAN] Liberando espaco em disco..."
sudo docker system prune -f
sudo docker image prune -a -f

echo "[CHECK] Verificando imagem Docker..."
echo "[PULL] Tentando baixar imagem pré-compilada da Artifact Registry..."
if ! sudo docker pull $IMG_NAME; then
    echo "[BUILD] Falha no Pull ou imagem inexistente. Iniciando Build local..."
    mkdir -p /tmp/lana_build
    cp /workspace/Dockerfile.v8_industrial /tmp/lana_build/Dockerfile
    cd /tmp/lana_build
    sudo docker build -t $IMG_NAME .
fi

# 1. Verificar/Instalar Motor Industrial
echo "[BOOT] Garantindo ambiente de GPU..."
if ! command -v nvidia-ctk &> /dev/null; then
    echo "[BOOT] Toolkit ausente. Instalando para garantir a entrega..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      sudo tee /etc/stderr | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

# 2. Puxar imagem industrial
echo "[BOOT] Sincronizando motor..."

# 2. Iniciar Motor Lana Industrial (Port-Less Mode)
echo "[BOOT] Iniciando Motor Lana Industrial..."
sudo docker stop $(sudo docker ps -q) 2>/dev/null

# Verificação de GPU
if ! nvidia-smi &> /dev/null; then
    echo "[ERRO] Driver NVIDIA não detectado ou GPU ausente."
    exit 1
fi

sudo docker run -d --rm --gpus all \
    --network host \
    -v /workspace:/workspace \
    -v /mnt/weights:/mnt/weights \
    $IMG_NAME \
    bash -c "cd /workspace/latentsync && python3 industrial_main.py"

echo "[BOOT] Docker disparado em modo Industrial (Ponte MCP Ativa)."
