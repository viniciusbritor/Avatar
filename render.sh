#!/bin/bash

# Ignição Neural v7.1.8 (Industrial Diamond Fix)

# 1. Configurações de Ambiente
DOCKER_IMAGE="us-west4-docker.pkg.dev/brasili-ia-news/avatars-repo/lana:v7.1"
WORK_DIR="/workspace"

# 2. Renderização (Comando Direto - Estilo v7.1.6 que funcionou)
sudo docker run --rm --gpus all \
  -e HF_HUB_ENABLE_HF_TRANSFER=1 \
  -e PYTHONUNBUFFERED=1 \
  -v ${WORK_DIR}/latentsync:/app \
  -v ${WORK_DIR}/latentsync/checkpoints:/app/checkpoints \
  -v ${WORK_DIR}:/workspace \
  -v ${WORK_DIR}/.cache:/root/.cache \
  -w /app \
  ${DOCKER_IMAGE} \
  scripts/inference.py \
  --unet_config_path "configs/unet/stage2.yaml" \
  --inference_ckpt_path "checkpoints/latentsync_unet.pt" \
  --guidance_scale 1.5 \
  --video_path "/workspace/lana_input.mp4" \
  --audio_path "/workspace/lana_audio.mp3" \
  --video_out_path "/workspace/temp/lana_v4_fixed.mp4"

# 3. Entrega Industrial
if [ -f "/workspace/temp/lana_v4_fixed.mp4" ]; then
    echo "SUCESSO: Video gerado com sucesso."
    gsutil cp /workspace/temp/lana_v4_fixed.mp4 gs://brasil-ai-avatars/lana_v4_fixed.mp4
else
    echo "ERRO: Video nao encontrado na saida."
fi
