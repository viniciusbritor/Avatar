#!/bin/bash
# Script de Limpeza Industrial - Projeto Jennifer (FinOps)

PROJECT_ID="brasili-ia-news"

echo "🚀 Iniciando faxina financeira nos recursos GCP..."

# 1. Deletar Cloud SQL (Economia de ~R$ 46,00/mês)
# Listar instâncias para garantir que o nome está correto
echo "🔍 Procurando instâncias de SQL..."
gcloud sql instances list --project=$PROJECT_ID

# [PERIGO] O comando abaixo deleta a instância permanentemente. 
# Substitua INSTANCE_NAME pelo nome listado acima (ex: lana-db).
# gcloud sql instances delete INSTANCE_NAME --project=$PROJECT_ID --quiet

# 2. Configurar Política de Limpeza no Artifact Registry
echo "🧹 Aplicando política de ciclo de vida no Artifact Registry..."
# Assumindo o repositório 'avatar-images' em 'us-east4'
# gcloud artifacts repositories set-cleanup-policies avatar-images \
#     --project=$PROJECT_ID --location=us-east4 \
#     --policy=infrastructure/registry_cleanup_policy.json

echo "✅ Script concluído. Execute os comandos comentados após confirmar os nomes dos recursos."
