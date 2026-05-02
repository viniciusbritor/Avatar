# Especificações Técnicas Operacionais — Avatar v3.1.6-r1

Este documento contém as definições técnicas para operação, manutenção e escalonamento do ecossistema.

## 1. Definições de API (Cérebro)
- **URL Base:** `https://avatar-api-ckzdqzo75q-ue.a.run.app`
- **Cloud Run Revision Atual:** `avatar-api-00071`
- **Endpoints Principais:**
    - `POST /produce`: Início do processo assíncrono.
    - `GET /status/{job_id}`: Consulta estado no Firestore.
    - `GET /health`: Diagnóstico de infraestrutura.
    - `POST /webhook/render-complete`: Ponto de retorno da GPU.
    - `POST /internal/render-worker`: Worker exclusivo do Cloud Tasks (roda orquestração em background thread).

## 2. Configurações de Nuvem (GCP)
- **Projeto:** `brasili-ia-news` (ID: `180096224219`)
- **Região Primária:** `us-east1`
- **VPC / Rede:** `default` (com acesso IAP para SSH).
- **Service Account (API):** `avatar-api-sa@brasili-ia-news.iam.gserviceaccount.com`
  - Permissões: Compute Admin, Cloud Tasks Enqueuer, Secret Manager Accessor, Firestore User.
- **Cloud Tasks Queue:** `avatar-render-queue` (us-east1, dispatch deadline: 1800s)
- **Firestore Collection:** `avatar_jobs`

## 3. Imagens Docker Oficiais (Artifact Registry)
- **API Image:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:latest`
  - Dockerfile: `api/Dockerfile` (Python 3.11-slim + gcloud CLI + FastAPI)
  - Entrypoint: `api/entrypoint.sh` (autentica via Secret Manager, sobe uvicorn com 4 workers)
- **Worker Image:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.9`
  - Dockerfile: `infra/Dockerfile.avatar-l4-v2.9` (CUDA 12.1 + PyTorch + Diffusers)

## 4. O Agente de Ponte (Local Bridge)
- **Script:** `src/sync_bridge.py`
- **Tecnologia:** Google Cloud Pub/Sub (Subscriber).
- **Missão:** Download automático via trigger instantâneo.
- **Configuração:** Deve rodar como serviço em background na máquina do usuário.

## 5. FinOps & Custos (Zero-Waste)
- **Cloud Run:** Cobrança apenas por requisição.
- **Compute Engine (L4):** `g2-standard-12` — Cobrança por segundo de uso (~$0.70/h).
- **GCS Fuse:** Evita custos de tráfego interno ao não baixar pesos de modelos entre regiões (Streaming).
- **Self-Destruction:** Shutdown em 120 minutos (dead man's switch) + Sentinela de inatividade de GPU (30 min).

## 6. Fixes Aplicados (02/05/2026)
1. `_find_existing_engines` usa gcloud CLI em vez de biblioteca compute_v1
2. `_run_ssh_cmd` sem `shell=True`, `echo y |`, `2>NUL`
3. `--command` sem aspas duplas escapadas (compatível com subprocess lista)
4. VM purgada em falha do bootstrap (`try/finally` com flag)
5. Docker image tag padronizada (`avatar-l4:v2.9`)
6. Engine com auto-detecção Linux/Windows (`CloudLanaEngine` vs `LanaIndustrialEngine`)
7. Bootstrap com pull de imagem em comando SSH separado (keepalive)
8. Codebase LatentSync sincronizada do GCS durante bootstrap
9. Instalação de `eva-decord` no container L4
10. Orquestrador roda em background thread (não bloqueia Cloud Run)
11. Uvicorn com 4 workers (API responde a health checks durante orquestração)

## 7. Checklist de Manutenção
1. Verificar cotas de GPU L4 anualmente ou em caso de aumento de demanda.
2. Garantir que a chave `API_SECRET_KEY` no Secret Manager não foi rotacionada sem atualizar a API.
3. Monitorar a fila `avatar-render-queue` para identificar gargalos de provisionamento.
4. Atualizar codebase LatentSync no bucket `gs://brasil-ai-avatars-vault/latentsync/` quando houver updates no repositório upstream.

---
*Status: Industrial v3.1.6-r1 — Correções de infraestrutura aplicadas, pipeline em validação final.*
