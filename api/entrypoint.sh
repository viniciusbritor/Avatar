#!/bin/bash
# entrypoint.sh — VM e2-micro (v3 — ADC nativo)
# Sem gcloud auth manual. Usa Application Default Credentials
# do metadata server. Robusto, sem dependências frágeis.
set -e
export HOME=/root

echo "[BOOT] FastAPI porta 8080 (ADC nativo)..."
exec python3 -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --timeout-keep-alive 3600 \
    --limit-concurrency 10 \
    --backlog 2048
