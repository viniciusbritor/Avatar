#!/bin/bash
set -e
echo "--- INICIANDO RENDERIZAÇÃO CORRIGIDA (DNA VINICIUS DONO) ---"
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync
cd /workspace/latentsync

# Executando a inferência com o vídeo mestre solicitado e voz Sarah Brasil
python3 scripts/inference.py \
    --unet_config_path "configs/unet/stage2.yaml" \
    --inference_ckpt_path "/mnt/weights/checkpoints/latentsync_unet.pt" \
    --video_path "assets/AVATAR_CUSTOM_V29_VINICIUS_DONO.mp4" \
    --audio_path "/workspace/input_audio.mp3" \
    --video_out_path "/workspace/cris_v1_vinicius_dono_output.mp4"

echo "--- RENDERIZAÇÃO CORRIGIDA CONCLUÍDA COM SUCESSO ---"
