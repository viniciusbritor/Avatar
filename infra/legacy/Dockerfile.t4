# Lana Industrial Engine - T4 Optimized Dockerfile (Plan B)
# Alinhado com a estratégia de resiliência soberana de Vinicius Brito

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

# Copiar definições fixas de bibliotecas
COPY requirements.txt .

# Instalação das bibliotecas industriais
# Nota: cu121 suporta T4 (sm_75) perfeitamente
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121

# Configurações Globais de Performance T4
ENV PYTHONUNBUFFERED=1
ENV LANA_GPU_ARCH=T4
ENV CUDA_VISIBLE_DEVICES=0

# O diretório de trabalho aponta para o HD externo de "Memória",
# que será montado em /workspace com `docker run -v`
WORKDIR /workspace

# Label para rastreabilidade industrial
LABEL project="Lana"
LABEL tier="Plan-B-T4"
