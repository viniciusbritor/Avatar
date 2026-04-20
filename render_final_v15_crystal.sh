#!/bin/bash
# Lana V15.5 - Crystal Gold Standard (CWD Fix)
echo "--- INICIANDO RENDERIZAÇÃO CRYSTAL CLEAR (v15.5) ---"

# 1. Garantir Backbone
/workspace/backbone_self_healing.sh || exit 1

# 2. Configuração de Caminhos
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib

# 3. Execução da Inferência a partir da raiz do pacote LatentSync
cd /workspace/latentsync

python3 scripts/inference.py \
    --unet_config_path "configs/unet/stage2.yaml" \
    --inference_ckpt_path "/workspace/latentsync/checkpoints/latentsync_unet.pt" \
    --guidance_scale 1.5 \
    --video_path "/workspace/lana_base_25fps.mp4" \
    --audio_path "/workspace/lana_audio_v7.mp3" \
    --video_out_path "/workspace/LANA_V15_GOLD.mp4"

echo "--- OPERAÇÃO CONCLUÍDA ---"
