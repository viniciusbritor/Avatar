#!/bin/bash
# provision_gold_disk.sh - Hidratação do Disco de Pesos (Operação Única)

DISK_NAME="lana-weights-v1"
ZONE="us-east1-c"
MOUNT_PATH="/mnt/weights"

echo "💿 Iniciando Hidratação do Disco $DISK_NAME..."

# 1. Formatar o disco (Apenas se for novo)
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/disk/by-id/google-weights-disk || echo "Disco já formatado."

# 2. Montar
sudo mkdir -p $MOUNT_PATH
sudo mount -o discard,defaults /dev/disk/by-id/google-weights-disk $MOUNT_PATH
sudo chmod a+w $MOUNT_PATH

# 3. Instalar Git LFS
echo "📦 Instalando Git LFS..."
sudo apt-get update && sudo apt-get install -y git-lfs
git lfs install

# 4. Baixar Pesos (LatentSync)
echo "📥 Baixando Pesos Reais (12GB)..."
cd $MOUNT_PATH
sudo rm -rf *
mkdir -p checkpoints configs
git clone https://huggingface.co/ByteDance/LatentSync-1.6 temp_models

# Mover arquivos essenciais
mv temp_models/latentsync_unet.pt checkpoints/
mv temp_models/stable_syncnet.pt checkpoints/
cp -rv temp_models/configs/* configs/
rm -rf temp_models

echo "✅ Hidratação Soberana Concluída."
ls -lh checkpoints/
