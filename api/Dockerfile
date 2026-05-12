# ─── Brasil AI Avatar API — Dockerfile (v4.5 — sem gcloud CLI, Python SDK nativo) ──────
# Imagem leve: ~400-500 MB. Sem gcloud CLI, sem ffmpeg, sem deps de GPU.

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app/api \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY api/ ./api/
COPY infra/boot/ ./infra/boot/

RUN chmod +x /app/api/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/app/api/entrypoint.sh"]