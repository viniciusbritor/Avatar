# ─── Brasil AI Avatar API — Dockerfile (Cloud Run Edition) ───────────────────
# Baseado em Python 3.10-slim. Instala o Google Cloud SDK para manter
# compatibilidade com gcloud compute ssh (Fase 2A).
# A Fase 2B futura migra para google-cloud-compute (SDK Python nativo).

FROM python:3.10-slim

# Metadados
LABEL maintainer="Brasil AI" \
      version="2.0.0" \
      description="Avatar API — Cloud Run"

# Instalar dependências do sistema + Google Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    openssh-client \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
       | tee /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
       | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python primeiro (cache Docker otimizado)
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar src/ (engine original — não modificado)
COPY src/ ./src/

# Copiar api/ (nova camada de API)
COPY api/ ./api/

# Copiar o startup script para dentro da imagem
# (usado pelo CloudLanaEngine para provisionar a GPU VM)
COPY infra/startup_arch4.sh ./infra/startup_arch4.sh

# Variáveis de ambiente padrão
ENV PYTHONPATH=/app/src:/app/api \
    STARTUP_SCRIPT_PATH=/app/infra/startup_arch4.sh \
    PORT=8080

# Expõe a porta padrão do Cloud Run
EXPOSE 8080

# Health check interno
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicialização
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
