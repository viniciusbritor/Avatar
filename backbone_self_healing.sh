#!/bin/bash
# Lana V15 - Backbone Self-Healing
echo "[BACKBONE] Verificando integridade dos pesos industriais..."

CKPT_DIR="/workspace/latentsync/checkpoints"
mkdir -p $CKPT_DIR/gfpgan

# 1. Verificar GFPGAN
if [ ! -f $CKPT_DIR/gfpgan/GFPGANv1.4.pth ]; then
    echo "[BACKBONE] GFPGAN ausente. Resgatando do backup GCS..."
    # Note: Using the authorized bucket we just populated
    gsutil cp gs://brasil-ia-lana-assets/models/GFPGANv1.4.pth $CKPT_DIR/gfpgan/
fi

# 2. Segurança: Impedir render se os modelos falharem
if [ ! -f $CKPT_DIR/gfpgan/GFPGANv1.4.pth ]; then
    echo "[FATAL] Falha crítica de Backbone. Abortando para evitar baixa qualidade."
    exit 1
fi

echo "[BACKBONE] Estados Verificados: CRYSTAL CLEAR READY."
