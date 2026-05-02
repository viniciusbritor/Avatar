# Especificações Técnicas Operacionais — Avatar v3.1.6-r2

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
- **Worker Image:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.10`
  - Dockerfile: `infra/Dockerfile.avatar-l4-v2.10` (CUDA 12.1 + PyTorch + todas deps LatentSync + código do projeto)
  - Arquitetura de layers otimizada: apt → torch → deps → código (cache eficiente)

## 4. O Agente de Ponte (Local Bridge)
- **Script:** `src/sync_bridge.py`
- **Tecnologia:** Polling no Firestore (sem dependência de Pub/Sub).
- **Missão:** Download automático via trigger.
- **Configuração:** Rodar sob demanda na máquina do usuário.
- **Modos:**
    - `python sync_bridge.py` — polling contínuo (5s)
    - `python sync_bridge.py --once` — processa pendentes e sai
    - `python sync_bridge.py --watch 30` — intervalo customizado

## 5. FinOps & Custos (Zero-Waste)
- **Cloud Run:** Cobrança apenas por requisição.
- **Compute Engine (L4):** `g2-standard-12` — Cobrança por segundo de uso (~$0.70/h).
- **GCS Fuse:** Evita custos de tráfego interno ao não baixar pesos de modelos entre regiões (Streaming).
- **Self-Destruction:** Shutdown em 120 minutos (dead man's switch) + Sentinela de inatividade de GPU (30 min).

## 6. Fixes Aplicados (02/05/2026)
1-15. (ver acima - correções de infraestrutura)
16. **v2.10:** Imagem L4 refatorada com layers otimizadas e cache eficiente
17. Todas as dependências LatentSync baked na imagem (sem pip install runtime)
18. Código do projeto (industrial_main.py, lipsync_pipeline.py) incluso na imagem L4
19. Bootstrap simplificado: sem downloads GCS de scripts, sem instalações pip
20. DOCKER_IMAGE consolidado (tag única v2.10), cloudbuild.yaml consistente

## 7. Estrutura do Dockerfile L4 (v2.10)
| Layer | Conteúdo | Quando rebuilda |
|---|---|---|
| 1. apt | ffmpeg, python3.10, git, libsndfile | Raramente |
| 2. PyTorch | torch + torchvision + torchaudio CUDA 12.1 | Upgrade CUDA/PyTorch |
| 3. ML Core | diffusers, transformers, insightface, onnxruntime | Upgrade de versões |
| 4. LatentSync Deps | eva-decord, accelerate, kornia, lws, imageio | Feature nova |
| 5. Servidor API | fastapi, uvicorn, google-cloud-storage | Raramente |
| 6. DeepCache | git+https://github.com/horseee/DeepCache.git | Mudança no upstream |
| 7. CÓDIGO | src/ (industrial_main, lipsync_pipeline, secrets_manager) | A CADA COMMIT (~5s) |

## 8. Checklist de Manutenção
1. Verificar cotas de GPU L4 anualmente ou em caso de aumento de demanda.
2. Garantir que a chave `API_SECRET_KEY` no Secret Manager não foi rotacionada sem atualizar a API.
3. Monitorar a fila `avatar-render-queue` para identificar gargalos de provisionamento.
4. Atualizar codebase LatentSync no bucket `gs://brasil-ai-avatars-vault/latentsync/` quando houver updates no repositório upstream.

---
*Status: Industrial v3.1.6-r2 — Layers otimizadas, deps baked, bootstrap simplificado.*
