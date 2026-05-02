#!/bin/bash
# entrypoint.sh — Brasil AI Avatar API (Cloud Run)
# Autentica o gcloud CLI usando a chave da SA armazenada no Secret Manager.

set -e

# Define o diretório de config do gcloud explicitamente
# Garante que o subprocess Python herde o mesmo CLOUDSDK_CONFIG
export CLOUDSDK_CONFIG=/root/.config/gcloud
export HOME=/root

echo "[BOOT] Buscando credenciais do Secret Manager via ADC..."

python3 -c "
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
resp = client.access_secret_version(
    name='projects/brasili-ia-news/secrets/avatar-api-sa-key/versions/latest'
)
with open('/tmp/sa-key.json', 'wb') as f:
    f.write(resp.payload.data)
print('[BOOT] Chave obtida do Secret Manager.')
"

# Autentica o gcloud CLI
gcloud auth activate-service-account \
    --key-file=/tmp/sa-key.json \
    --quiet

gcloud config set project brasili-ia-news --quiet
gcloud config set compute/region us-east1 --quiet

rm -f /tmp/sa-key.json

# Verificação: confirma que o gcloud está autenticado
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
echo "[BOOT] gcloud autenticado como: $ACCOUNT"

# Exporta o CLOUDSDK_CONFIG para que subprocessos Python herdem
export CLOUDSDK_CONFIG
export HOME

echo "[BOOT] Iniciando servidor FastAPI..."

# Passa as variáveis de ambiente explicitamente para o processo uvicorn
exec env CLOUDSDK_CONFIG="$CLOUDSDK_CONFIG" HOME="$HOME" \
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --timeout-keep-alive 3600
