#!/bin/bash
echo "=========================================================="
echo "🚀 INICIANDO LANA INDUSTRIAL NO MODO DOCKER (ZERO-WASTE) 🚀"
echo "=========================================================="

# 1. Autenticação na Fábrica de Imagens do GCP
gcloud auth configure-docker us-east1-docker.pkg.dev --quiet

# 2. Execução da Imagem Imutável Acoplando a Memória (Disco Voador de 100GB)
echo "Acoplando Disco de Memória e Instalando a VRAM..."
docker run --rm --gpus all \
  -v /workspace:/workspace \
  us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0 \
  bash -c "cd /workspace/latentsync && python3 -m latentsync.scripts.inference \
    --unet_config_path configs/unet/stage2.yaml \
    --inference_ckpt_path checkpoints/latentsync_unet.pt \
    --guidance_scale 1.5 \
    --video_path /workspace/lana_base_25fps.mp4 \
    --audio_path /workspace/lana_audio_v7.mp3 \
    --video_out_path /workspace/LANA_V8.2_CRYSTAL_CLEAR_DOCKER.mp4"

echo "=========================================================="
echo "💎 VÍDEO CONCLUÍDO COM SUCESSO! 💎"
echo "=========================================================="
