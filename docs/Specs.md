# Especificacoes Tecnicas Operacionais — Avatar v3.2.0

## 1. API (Cerebro)
- **Host:** VM e2-micro `lana-api` (us-east1-b)
- **URL:** `http://35.237.48.76:8080` (IP efemero, verificar ao recriar VM)
- **Endpoints:**
    - `POST /produce`: Enfileira producao (TTS + Firestore + spawn GPU)
    - `GET /status/{job_id}`: Consulta estado no Firestore
    - `GET /health`: Diagnostico da API
    - `POST /webhook/render-complete`: Callback da GPU
- **Tempo de resposta:** ~5-8s (fire-and-forget, nao espera GPU)
- **Entrypoint:** `api/entrypoint.sh` — ADC nativo, sem gcloud auth manual
- **Workers:** 1 uvicorn worker (e2-micro: 2 vCPU, 1 GB RAM)

## 2. GPU (Motor)
- **Hardware:** `g2-standard-12` (NVIDIA L4, 22 GB VRAM)
- **Spawn:** `_spawn_gpu()` em background thread, retry 3x, 13 zonas
- **Auto-bootstrap:** `startup_arch4.sh` — Docker, NVIDIA, GCS Fuse, pull imagem, run container
- **Auto-orquestra:** `industrial_main.py` faz polling Firestore continuo (10s)
- **Render:** `guidance_scale=2.5`, `inference_steps=40`, seed aleatorio, mascara dilatada 7px
- **Shutdown:** Dead man's switch 120 min (startup script) + idle via poller (a implementar)

## 3. GCP
- **Projeto:** `brasili-ia-news`
- **Regiao:** `us-east1`
- **VPC:** `default`
- **VM API SA:** `180096224219-compute@developer.gserviceaccount.com`
- **GPU SA:** mesma (compute default)
- **Firestore:** `avatar_jobs`
- **GCS Vault:** `gs://brasil-ai-avatars-vault`
- **GCS Weights:** `gs://lana-weights-universal` (GCS Fuse em `/mnt/weights`)

## 4. Imagens Docker (Artifact Registry)
- **API:** `avatar-api:latest` (Python 3.11-slim + gcloud CLI + FastAPI)
- **GPU:** `avatar-l4:v2.10-golden` (CUDA 12.1 + LatentSync submodule + todas deps)
  - Dockerfile: `infra/Dockerfile.avatar-l4-v2.10-golden`
  - Fonte LatentSync: `latentsync/` (git submodule `bytedance/LatentSync`)
  - Patches: `decord`→`eva-decord`, `DeepCache` do git, mascara dilatada

## 5. Local Bridge
- **Script:** `src/sync_bridge.py`
- **Modo:** Polling Firestore (sem Pub/Sub)
- **Download:** `gsutil cp` direto (ADC nao configurado localmente)

## 6. FinOps & Custos
| Recurso | Custo |
|---|---|
| VM e2-micro (24/7) | ~$6/mes |
| GPU L4 (sob demanda) | ~$0.70/h |
| Dead man's switch | 120 min max |
| Idle shutdown | A implementar (15 min) |

## 7. CI/CD
| YAML | Proposito | Tempo |
|---|---|---|
| `cloudbuild-api.yaml` | Build + push API | ~5 min |
| `cloudbuild-l4-golden.yaml` | Build golden L4 | ~20 min |
| `cloudbuild-l4.yaml` | Build L4 (antigo) | ~15 min |
| `cloudbuild-all.yaml` | Ambos | ~25 min |
| `cloudbuild-api-only.yaml` | API legado (Cloud Run) | Deprecated |

## 8. Parametros de Render (v2.10)
| Parametro | Valor | Efeito |
|---|---|---|
| `guidance_scale` | 2.5 | Fidelidade boca-audio |
| `inference_steps` | 40 | Qualidade da difusao |
| `seed` | aleatorio | Variacao natural |
| `mascara` | dilatada 7px | Transicao boca-rosto |

## 9. Checklist
1. GPU rodando? `gcloud compute instances list --filter="name~lana-engine-"`
2. VM API online? `curl http://35.237.48.76:8080/health`
3. Fila de jobs? Firestore console > `avatar_jobs`
4. Custos? `gcloud compute instances list` — desligar GPUs ociosas

---
*Status: Industrial v3.2.0 — VM e2-micro, golden image, fire-and-forget, GPU auto-orquestravel.*
