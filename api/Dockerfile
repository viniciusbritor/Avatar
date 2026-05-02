# ─── Brasil AI Avatar API — Dockerfile (Cloud Run Edition v5 — Official) ──────
# Focado em estabilidade industrial: Python 3.11 + Gcloud SDK via APT

FROM python:3.11-slim

# Configurações de ambiente
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/api \
    PORT=8080

WORKDIR /app

# Instalação de dependências do sistema e Gcloud SDK via repositório oficial
RUN apt-get update && apt-get install -y \
    curl \
    git \
    openssh-client \
    ffmpeg \
    libsm6 \
    libxext6 \
    procps \
    netcat-openbsd \
    ca-certificates \
    gnupg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update && apt-get install -y google-cloud-cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python (Aproveitando cache do Docker)
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação e infraestrutura
COPY src/ ./src/
COPY api/ ./api/
COPY infra/ ./infra/

# Garantir permissões e integridade
RUN chmod +x /app/api/entrypoint.sh

EXPOSE 8080

# O Maestro inicia com runtime garantido e autenticação via Secret Manager
ENTRYPOINT ["/app/api/entrypoint.sh"]
