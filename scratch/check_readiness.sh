#!/bin/bash
echo "--- AGENTE ANTIGRAVITY: RELATÓRIO DE PRONTIDÃO ---"

# 1. Check de Bibliotecas
echo -n "Python Libs (Torch, Diffusers, FastAPI, Kornia)... "
python3 -c "import torch, diffusers, kornia, fastapi, requests, cv2, PIL; print('OK')" || echo "FALHA"

# 2. Check de GPU
echo -n "NVIDIA L4 Driver... "
nvidia-smi --query-gpu=name --format=csv,noheader || echo "FALHA"

# 3. Check de Disco (Gold Disk)
echo -n "Gold Disk Weights (/mnt/weights)... "
if [ -f "/mnt/weights/checkpoints/latentsync_unet.pt" ]; then
    echo "OK (Pesos Localizados)"
else
    echo "FALHA (Disco não montado ou arquivos ausentes)"
fi

# 4. Check de Workspace
echo -n "LatentSync Script... "
if [ -f "/workspace/latentsync/scripts/inference.py" ]; then
    echo "OK"
else
    echo "FALHA"
fi

echo "------------------------------------------------"
