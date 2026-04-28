#!/bin/bash
# Lana Industrial Startup Script - Architecture 4 (Stateless + GCS Fuse)
# Executado como ROOT no primeiro boot da VM.

echo "--- INICIANDO BOOT INDUSTRIAL ARCH 4 ---"

# 1. DEAD MAN'S SWITCH (Auto-destruição em 60 minutos)
# Garante que a máquina morra mesmo se o orquestrador falhar.
echo "sudo shutdown -P +120" | at now 2>/dev/null || (apt-get update && apt-get install -y at && echo "sudo shutdown -P +120" | at now)

# 2. INSTALAR DOCKER E NVIDIA TOOLKIT (Se não existirem)
if ! command -v docker &> /dev/null; then
    apt-get update
    apt-get install -y docker.io
    systemctl start docker
    systemctl enable docker
fi

if ! command -v nvidia-ctk &> /dev/null; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update && apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# 3. INSTALAR GCS FUSE
if ! command -v gcsfuse &> /dev/null; then
    export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
    echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
    apt-get update
    apt-get install -y gcsfuse
fi

# 4. MONTAR BUCKET DE PESOS (Streaming Mode)
mkdir -p /mnt/weights
chmod 777 /mnt/weights
# Montar o bucket lana-weights-universal/checkpoints em /mnt/weights
# Usamos --allow-other para que o Docker possa ler os arquivos
gcsfuse -o allow_other --only-dir checkpoints lana-weights-universal /mnt/weights

# 5. PREPARAR WORKSPACE
mkdir -p /workspace
chmod 777 /workspace

# 6. CONFIGURAR DOCKER AUTH (Artifact Registry)
# Isso permite que o docker pull funcione sem intervenção manual
# Nota: A VM precisa ter o escopo cloud-platform ativado na criação.
gcloud auth configure-docker us-east1-docker.pkg.dev --quiet

echo "--- BOOT FINALIZADO: PRONTO PARA PRODUÇÃO ---"
