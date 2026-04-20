FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Configurações para não travar em interações do apt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Instalação das bibliotecas nativas de video (FFMPEG), SO e Python 3.10
RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3.10 \
    python3-pip \
    python3.10-dev \
    git \
    wget \
    ffmpeg \
    libavcodec-dev \
    libsm6 \
    libxext6 \
    libgl2ps-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Definindo o Python padrão
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade Pip
RUN pip3 install --no-cache-dir --upgrade pip

# Instalação do Base Pytorch compatível com CUDA 12.1
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Instalação do Ecossistema LatentSync e Ferramentas Mapeadas na Nuvem
RUN pip3 install --no-cache-dir \
    DeepCache \
    insightface \
    facexlib \
    decord \
    kornia \
    lpips \
    imageio \
    imageio-ffmpeg \
    omegaconf \
    diffusers \
    transformers \
    accelerate \
    einops \
    safetensors \
    onnxruntime-gpu \
    nvidia-cudnn-cu12 \
    librosa \
    numpy<2 \
    opencv-python-headless \
    huggingface-hub

# Configurações Globais de Performance e Despejo de Erros
ENV PYTHONUNBUFFERED=1

# O diretório de trabalho aponta para o HD externo de "Memória",
# que será montado em /workspace com `docker run -v`
WORKDIR /workspace
