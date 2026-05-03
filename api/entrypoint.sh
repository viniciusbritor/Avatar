#!/bin/bash
# entrypoint.sh — Brasil AI Avatar API (VM e2-micro)
# Usa a service account default da VM (sem Secret Manager dance).

set -e

export HOME=/root

echo "[BOOT] Autenticando gcloud via service account da VM..."

gcloud auth activate-service-account --key-file=/dev/null 2>/dev/null || true
gcloud config set project brasili-ia-news --quiet
gcloud config set compute/region us-east1 --quiet

ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "default")
echo "[BOOT] gcloud: $ACCOUNT"

echo "[BOOT] Iniciando FastAPI na porta 8080..."

exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --timeout-keep-alive 3600
