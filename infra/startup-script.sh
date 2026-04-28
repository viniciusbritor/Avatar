#!/bin/bash
# Lana Industrial Engine v18.11 - Startup Script Soberano
# Objetivo: Automação Stateless, Persistência Global & Gestão de Custos L4/T4

echo "[LANA] Iniciando provisionamento industrial (v18.11)..."

# 1. Preparar Ambiente
mkdir -p /workspace/infra
mkdir -p /workspace/outputs
mkdir -p /workspace/logs

# 2. Sincronizar scripts do GCS (ou Git se configurado)
# Em ambiente GCP real, usaríamos gsutil aqui para garantir a versão mais recente.
# echo "[LANA] Sincronizando scripts de infraestrutura..."
# gsutil cp gs://brasil-ia-lana-assets/infra/* /workspace/infra/

# 3. Executar Boot Industrial (Auto-detecção L4/T4)
chmod +x /workspace/infra/*.sh
bash /workspace/infra/boot_industrial_v18.sh

echo "[LANA] Motor pronto. Monitoramento de custos e dashboard ATIVOS."
