# Arquitetura — Brasil AI Avatar (LANA) v3.2.1

## Visão Geral

Sistema autônomo de produção de avatares de vídeo com IA, operando em Google Cloud Platform com filosofia **Zero-Waste** (GPUs sob demanda, auto-destruição).

```
┌──────────────────────────────────────────────────────────────┐
│  USUÁRIO                                                     │
│  POST /produce ──► VM e2-micro API (IP fixo 35.231.46.76)   │
│                      │                                       │
│                      ├─► ElevenLabs TTS (áudio)              │
│                      │                                       │
│                      ├─► Firestore (avatar_jobs)             │
│                      │     └─► job queued                    │
│                      │                                       │
│                      ├─► gcloud CLI (Compute Engine)         │
│                      │     └─► NVIDIA L4 VM (g2-standard-12)│
│                      │           ├─ startup_arch4.sh          │
│                      │           │  (Docker + NVIDIA Toolkit) │
│                      │           │  (GCS Fuse mount)         │
│                      │           │  (Dead Man's Switch 90min) │
│                      │           │  (docker cp src + latentsync)│
│                      │           └─ docker run lana-engine    │
│                      │              └─ industrial_main.py     │
│                      │                                       │
│                      └─► Webhook ← GPU notifica API          │
│                          └─ Firestore (status: completed)    │
└──────────────────────────────────────────────────────────────┘

Fluxo de Renderização (GPU L4):
┌──────────────────────────────────────────────────────────────┐
│  Industrial Engine (Docker container, port 8080)             │
│  poll_pending_jobs() → Firestore (status=queued)             │
│    └─► Audio Download (GCS)                                  │
│    └─► LatentSync Inference (scripts/inference.py)           │
│    └─► GFPGAN Face Restoration                               │
│    └─► FFmpeg Mux (audio + video)                            │
│    └─► Upload result → GCS (outputs/avatar_{timestamp}.mp4) │
│    └─► Webhook → http://35.231.46.76:8080/webhook/render-complete│
│    └─► Touch /workspace/idle_now (hint shutdown)             │
└──────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### Cérebro (VM e2-micro — IP fixo)
| Arquivo | Função |
|---------|--------|
| `api/main.py` | FastAPI server: POST /produce, GET /status, webhook handler |
| `api/cloud_engine.py` | CloudLanaEngine: subclasse Linux do orquestrador de infra |
| `api/secrets_manager.py` | Abstração Secret Manager + fallback para env vars |

### Orquestrador (src/)
| Arquivo | Função |
|---------|--------|
| `src/agente_lana_orchestrator.py` | LanaIndustrialEngine + AgenteLanaOrchestrator: provisionamento GPU, TTS, render dispatch |
| `src/industrial_main.py` | FastAPI server dentro do container L4: polling Firestore, executa LatentSync |
| `src/lipsync_pipeline.py` | Pipeline LatentSync: diffusion model para lip sync |
| `src/sync_bridge.py` | Ponte local: download automático de vídeos concluídos do GCS |

### Infraestrutura (infra/)
| Arquivo | Função |
|---------|--------|
| `infra/boot/startup_arch4.sh` | Script de boot da GPU L4: Docker, NVIDIA toolkit, GCS Fuse, docker cp código, container |
| `infra/boot/startup-e2-micro.sh` | Script de boot da VM API: Docker, systemd unit, auto-update cron |
| `infra/services/lana-api.service` | Systemd unit: API sobrevive a restart de VM e crash |
| `infra/docker/Dockerfile.avatar-l4-v2.10-golden` | Imagem Docker GPU: CUDA 12.1 + PyTorch + Diffusers + LatentSync |
| `infra/legacy/lana-finops-sentinel.sh` | Watchdog de inatividade (legado, substituído pelo Sentinel HOST no startup_arch4.sh) |

### Deploy
| Arquivo | Função |
|---------|--------|
| `cloudbuild-api.yaml` | Cloud Build: build + push imagem API → Artifact Registry |
| `api/Dockerfile` | Imagem API: Python 3.11 + gcloud CLI |

## Fluxo de Dados (Text-to-Video)

1. `POST /produce` → ElevenLabs TTS (voz Matilda pt-BR) → upload GCS → Firestore (status: queued)
2. Background thread: provisiona VM L4 na zona com capacidade (13 zonas globais)
3. Bootstrap: Docker pull golden image → docker cp código → docker run → industrial_main.py
4. GPU polling: Firestore WHERE status=queued → baixa áudio → LatentSync → GFPGAN → FFmpeg
5. Upload GCS: `gs://brasil-ai-avatars-vault/outputs/avatar_{timestamp}.mp4`
6. Webhook: notifica API → Firestore (status: completed)
7. sync_bridge.py: polling local → download automático para `sucesso/`
8. GPU: idle detection → auto-shutdown (Dead Man Switch 90min)

## Buckets GCS
| Bucket | Conteúdo |
|--------|----------|
| `brasil-ai-avatars-vault` | Vídeos output, áudios TTS |
| `lana-weights-universal` | Checkpoints do modelo, assets de vídeo (templates) |

## Zonas L4 (ordem de preferência)
`us-east1-c → us-west4-a → us-east1-d → us-east4-a → us-west1-a → us-central1-a → us-east5-a → us-south1-a → europe-west4-a → europe-west1-b → europe-west6-b → asia-east1-a → northamerica-northeast1-b`
