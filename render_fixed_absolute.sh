#!/bin/bash
echo "--- INICIANDO RENDERIZAÇÃO FINAL ABSOLUTA (v12.7) ---"
# Configuração de Caminhos Industriais
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib

cd /workspace
echo "--- INICIANDO INFERÊNCIA CRYSTAL CLEAR (v8.2) ---"

# Execução do LatentSync com Caminhos Absolutos Confirmados
python3 -m latentsync.scripts.inference \
    --unet_config_path /workspace/latentsync/configs/unet/second_stage.yaml \
    --inference_ckpt_path /workspace/latentsync/checkpoints/latentsync_unet.pt \
    --guidance_scale 1.5 \
    --video_path /workspace/lana_base_25fps.mp4 \
    --audio_path /workspace/lana_audio_v7.mp3 \
    --video_out_path /workspace/LANA_V8.2_CRYSTAL_CLEAR.mp4 \
    --box_padding 0 0 0 0

echo "--- OPERAÇÃO CONCLUÍDA COM SUCESSO ---"
