#!/bin/bash
# Script de Resgate Lana v8.2
echo "Iniciando Soldagem de GPU..."
sudo docker exec -u root $(sudo docker ps -q) /bin/bash -c "pip install nvidia-cudnn-cu12"
echo "GPU Integrada. Iniciando Renderização v8.2..."
sudo bash /workspace/render.sh > /tmp/render_v8.2.log 2>&1
echo "Operação Concluída."
