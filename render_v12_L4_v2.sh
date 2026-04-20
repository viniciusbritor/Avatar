#!/bin/bash
echo "--- INICIANDO OPERAÇÃO CRYSTAL CLEAR (v12.0) ---"
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib
cd /workspace
python3 -m latentsync.scripts.inference \
    --unet_config_path "configs/unet/second_stage.yaml" \
    --inference_ckpt_path "checkpoints/latentsync_unet.pt" \
    --guidance_scale 1.5 \
    --video_path "lana_base_25fps.mp4" \
    --audio_path "lana_audio_v7.mp3" \
    --video_out_path "LANA_V8.2_CRYSTAL_CLEAR.mp4" \
    --box_padding 0 0 0 0
echo "--- RENDERIZAÇÃO CONCLUÍDA COM SUCESSO ---"
