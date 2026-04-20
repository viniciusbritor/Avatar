#!/bin/bash

# Configurações - ALtere conforme seu projeto
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1" # Sugerida para disponibilidade de L4
SERVICE_NAME="avatar-efemero"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
BUCKET_NAME="brasil-ai-avatars"

echo "🚀 Iniciando Deploy do Avatar Efêmero: $SERVICE_NAME"

# 1. Habilitar APIs necessárias
echo "📦 Habilitando APIs..."
gcloud services enable run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com

# 2. Criar Bucket (se não existir)
if ! gsutil ls -b gs://$BUCKET_NAME > /dev/null 2>&1; then
    echo "Creating bucket $BUCKET_NAME..."
    gsutil mb -l $REGION gs://$BUCKET_NAME
fi

# 3. Build da Imagem no Cloud Build (para ser mais rápido e não depender local)
echo "🔨 Construindo imagem Docker no Cloud..."
gcloud builds submit --tag $IMAGE_NAME .

# 4. Deploy no Cloud Run com GPU
echo "🚀 Fazendo deploy no Cloud Run com GPU L4..."
gcloud beta run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --no-allow-unauthenticated \
    --cpu 4 \
    --memory 16Gi \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --timeout 3600 \
    --set-env-vars GCP_BUCKET_NAME=$BUCKET_NAME \
    --max-instances 2 \
    --min-instances 0 \
    --no-zonal-redundancy

echo "✅ Deploy concluído!"
echo "🔗 URL do serviço: $(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')"
