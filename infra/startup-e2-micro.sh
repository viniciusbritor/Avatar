#!/bin/bash
# Lana API Startup Script — VM e2-micro
# Arquitetura Zero-Cloud-Run: VM fixa 24/7, comunicação HTTP direta na VPC.

echo "--- INICIANDO LANA API (e2-micro) ---"

# 1. Instalar Docker se não existir
if ! command -v docker &> /dev/null; then
    apt-get update
    apt-get install -y docker.io
    systemctl start docker
    systemctl enable docker
fi

# 2. Autenticar Artifact Registry
gcloud auth configure-docker us-east1-docker.pkg.dev --quiet

# 3. Pull e rodar container da API
docker rm -f lana-api 2>/dev/null
docker pull us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest

docker run -d --name lana-api \
    --restart unless-stopped \
    --network host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e PORT=8080 \
    us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest \
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --timeout-keep-alive 3600

echo "--- LANA API PRONTA — porta 8080 ---"
