# ─── Brasil AI Avatar API — Dockerfile (Cloud Run Edition v4) ─────────────────
# Multi-stage: Python deps no Stage 1, google/cloud-sdk no Stage 2.
# Entrypoint autentica o gcloud via SA key do Secret Manager antes de iniciar.

FROM python:3.10-slim AS python-builder
WORKDIR /install
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install/packages -r requirements.txt

FROM google/cloud-sdk:slim

# Instalar Python 3 disponível no Debian Trixie
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openssh-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copiar packages Python do stage anterior
COPY --from=python-builder /install/packages /usr/local

WORKDIR /app

# Instalar dependências (com fallback para Debian Trixie)
COPY api/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages 2>/dev/null || \
    pip3 install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY api/ ./api/
COPY infra/startup_arch4.sh ./infra/startup_arch4.sh

# Tornar o entrypoint executável
RUN chmod +x /app/api/entrypoint.sh

# Variáveis de ambiente
ENV PYTHONPATH=/app/src:/app/api \
    STARTUP_SCRIPT_PATH=/app/infra/startup_arch4.sh \
    PORT=8080

EXPOSE 8080

# Usa o entrypoint que autentica o gcloud antes de iniciar o servidor
CMD ["/app/api/entrypoint.sh"]
