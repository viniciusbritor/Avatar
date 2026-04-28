#!/bin/bash
# Script de preparação industrial para T4 (Plan B)
# Alinhado com a estratégia "Zero-Waste" de Vinicius Brito

echo "[LANA] Iniciando instalação de drivers e toolkit para T4..."

# 1. Instalar Drivers NVIDIA (headless)
sudo apt-get update
sudo apt-get install -y ubuntu-drivers-common
sudo ubuntu-drivers autoinstall

# 2. Instalar Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 3. Instalar NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# 4. Configurar Docker Runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo "[LANA] Driver e Toolkit instalados. Reiniciando para aplicar drivers..."
sudo reboot
