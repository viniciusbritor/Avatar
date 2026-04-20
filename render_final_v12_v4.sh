#!/bin/bash
echo "--- INICIANDO FULL STERILIZATION (v12.4) ---"
# Instalação das bibliotecas de visão computacional detectadas
pip install -q omegaconf matplotlib diffusers transformers accelerate einops safetensors onnxruntime-gpu nvidia-cudnn-cu12 librosa kornia lpips imageio imageio-ffmpeg

# Configuração de Caminhos
export PYTHONPATH=$PYTHONPATH:/workspace/latentsync
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib

cd /workspace
echo "--- INICIANDO RENDERIZAÇÃO CRYSTAL CLEAR ---"
# Execução da Inferência
python3 -m latentsync.scripts.inference \
    --unet_config_path "configs/unet/second_stage.yaml" \
    --inference_ckpt_path "checkpoints/latentsync_unet.pt" \
    --guidance_scale 1.5 \
    --video_path "lana_base_25fps.mp4" \
    --audio_path "lana_audio_v7.mp3" \
    --video_out_path "LANA_V8.2_CRYSTAL_CLEAR.mp4" \
    --box_padding 0 0 0 0
echo "--- OPERAÇÃO CONCLUÍDA ---"
