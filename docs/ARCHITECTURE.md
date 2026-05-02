# Arquitetura — Brasil AI Avatar (LANA) v3.1.6-r1

## Visão Geral

Sistema autônomo de produção de avatares de vídeo com IA, operando em Google Cloud Platform com filosofia **Zero-Waste** (GPUs sob demanda, auto-destruição).

```
┌──────────────────────────────────────────────────────────────┐
│  USUÁRIO                                                     │
│  POST /produce ──► Cloud Run API (FastAPI, us-east1)         │
│                      │                                       │
│                      ├─► Cloud Tasks Queue                   │
│                      │     └─► /internal/render-worker       │
│                      │           (background thread)          │
│                      │                                       │
│                      ├─► gcloud CLI (Compute Engine)         │
│                      │     └─► NVIDIA L4 VM (g2-standard-12)│
│                      │           ├─ startup_arch4.sh          │
│                      │           │  (Docker + NVIDIA Toolkit) │
│                      │           │  (GCS Fuse mount)         │
│                      │           │  (Dead Man's Switch)      │
│                      │           └─ bootstrap_v18            │
│                      │              ├─ GCS sync (LatentSync) │
│                      │              ├─ Docker pull (15GB)    │
│                      │              ├─ Docker run             │
│                      │              ├─ pip install eva-decord │
│                      │              └─ industrial_main.py     │
│                      │                                       │
│                      └─► Firestore (job state)               │
│                          └─ GET /status/{job_id}             │
└──────────────────────────────────────────────────────────────┘

Fluxo de Renderização (GPU L4):
┌──────────────────────────────────────────────────────────────┐
│  Industrial Engine (Docker container, port 8080)             │
│  POST /clips                                                 │
│    └─► Audio Download (GCS)                                  │
│    └─► LatentSync Inference (scripts/inference.py)           │
│    └─► FFmpeg Mux (audio + video)                            │
│    └─► Upload result → GCS (outputs/final_{job_id}.mp4)     │
│    └─► Webhook → Cloud Run /webhook/render-complete          │
│    └─► Touch /workspace/idle_now (Sentinel)                  │
└──────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### Cérebro (Cloud Run)
| Arquivo | Função |
|---------|--------|
| `api/main.py` | FastAPI server: endpoints REST, Cloud Tasks integration, Firestore |
| `api/cloud_engine.py` | CloudLanaEngine: subclasse Linux do orquestrador de infra |
| `api/entrypoint.sh` | Autenticação gcloud via Secret Manager, inicia uvicorn (4 workers) |
| `api/secrets_manager.py` | Abstração Secret Manager + fallback para env vars |

### Orquestrador (src/)
| Arquivo | Função |
|---------|--------|
| `src/agente_lana_orchestrator.py` | LanaIndustrialEngine + AgenteLanaOrchestrator: provisionamento GPU, bootstrap, TTS, render dispatch |
| `src/industrial_main.py` | FastAPI server dentro do container L4: recebe jobs de render, executa LatentSync |
| `src/lipsync_pipeline.py` | Pipeline LatentSync: diffusion model para lip sync |
| `src/sync_bridge.py` | Ponte Pub/Sub: download automático de vídeos concluídos |

### Infraestrutura (infra/)
| Arquivo | Função |
|---------|--------|
| `infra/startup_arch4.sh` | Script de boot da VM: Docker, NVIDIA toolkit, GCS Fuse |
| `infra/Dockerfile.avatar-l4-v2.9` | Imagem Docker GPU: CUDA 12.1 + PyTorch + Diffusers + todas deps Python |
| `infra/lana-finops-sentinel.sh` | Watchdog de inatividade: desliga VM após 30min sem uso de GPU |

### Deploy
| Arquivo | Função |
|---------|--------|
| `cloudbuild.yaml` | Cloud Build: build das imagens Docker + deploy Cloud Run |
| `api/Dockerfile` | Imagem API: Python 3.11 + gcloud CLI |

## Fluxo de Dados (Text-to-Video)

1. `POST /produce` → Firestore (status: queued) → Cloud Tasks enfileira
2. Cloud Tasks → `POST /internal/render-worker` → background thread
3. Thread: provisiona VM L4 na zona com capacidade
4. Bootstrap: Docker pull → run → decord install → start industrial_main.py
5. Áudio: ElevenLabs TTS (voz Sarah) → upload GCS
6. Render: HTTP POST /clips na GPU → LatentSync → FFmpeg → upload GCS
7. Webhook: notifica Cloud Run → Firestore (status: completed)
8. Sentinel: VM se auto-destrói após inatividade

## Buckets GCS
| Bucket | Conteúdo |
|--------|----------|
| `brasil-ai-avatars-vault` | Vídeos output, scripts, DB, codebase LatentSync |
| `lana-weights-universal` | Checkpoints do modelo, assets de vídeo (templates) |

## Zonas L4 (ordem de preferência)
`us-east1-c → us-west4-a → us-east1-d → us-east4-a → us-west1-a → us-central1-a → us-east5-a → us-south1-a → europe-west4-a → europe-west1-b → europe-west6-b → asia-east1-a → northamerica-northeast1-b`
