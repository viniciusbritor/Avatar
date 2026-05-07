#!/bin/bash
# Script de Preparação do Container Lana v2.7
echo "[PREP] Iniciando Preparação do Container..."

# 1. Sincronizar scripts
cp /workspace/industrial_main.py /workspace/latentsync/industrial_main.py
cd /workspace/latentsync

# 2. Instalar dependências extras se necessário
pip install --no-cache-dir -r /workspace/requirements.txt

# 3. Aplicar Patch no BasicSR (Fix de compatibilidade Torchvision)
sed -i 's/torchvision.transforms.functional_tensor/torchvision.transforms.functional/' /usr/local/lib/python3.10/dist-packages/basicsr/data/degradations.py

echo "[PREP] Container pronto para inferência."
