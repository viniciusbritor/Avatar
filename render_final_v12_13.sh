#!/bin/bash
echo "--- INICIANDO RENDERIZAÇÃO INDUSTRIAL (v12.13) ---"

# Ajuste Crítico de Visibilidade de Bibliotecas
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync:/home/vinic/.local/lib/python3.10/site-packages
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib

cd /workspace
echo "--- INICIANDO INFERÊNCIA CRYSTAL CLEAR (v8.2) ---"

# Execução do LatentSync com Nomes de Arquivos Verificados
python3 -m latentsync.scripts.inference \
    --unet_config_path /workspace/latentsync/configs/unet/stage2.yaml \
    --inference_ckpt_path /workspace/latentsync/checkpoints/latentsync_unet.pt \
    --guidance_scale 1.5 \
    --video_path /workspace/lana_base_25fps.mp4 \
    --audio_path /workspace/lana_audio_v7.mp3 \
    --video_out_path /workspace/LANA_V8.2_CRYSTAL_CLEAR.mp4

echo "--- OPERAÇÃO CONCLUÍDA ---"
