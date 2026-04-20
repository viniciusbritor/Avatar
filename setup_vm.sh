#!/bin/bash
set -e

echo "=== Iniciando Setup do Motor LANA no GCE ==="

# 1. Instalar Docker
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# 2. Instalar NVIDIA Container Toolkit
if ! command -v nvidia-ctk &> /dev/null; then
    echo "Instalando NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
      && sudo apt-get update \
      && sudo apt-get install -y nvidia-container-toolkit
    
    echo "Reiniciando Docker para aplicar NVIDIA Toolkit..."
    sudo systemctl restart docker
fi

# 3. Preparar Diretorio de Checkpoints
echo "Preparando volumes..."
sudo mkdir -p /app/checkpoints
sudo chmod 777 /app/checkpoints

echo "=== Setup Concluido! ==="
