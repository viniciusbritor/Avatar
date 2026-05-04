# Especificacoes Tecnicas Operacionais — Avatar v3.2.0 (PRODUCAO)

## 1. API (Cerebro)
- **Host:** VM e2-micro `lana-api` (us-east1-b)
- **IP Fixo:** `35.231.46.76`
- **Endpoints:**
    - `POST /produce`: Enfileira producao (TTS + Firestore + spawn GPU) — ~5s
    - `GET /status/{job_id}`: Consulta estado no Firestore
    - `GET /health`: Diagnostico da API
    - `POST /webhook/render-complete`: Callback da GPU
- **Entrypoint:** `api/entrypoint.sh` — ADC nativo, sem gcloud auth manual
- **Workers:** 1 uvicorn (e2-micro: 2 vCPU, 1 GB RAM)

## 2. GPU (Motor L4)
- **Hardware:** `g2-standard-12` (NVIDIA L4, 22 GB VRAM)
- **Spawn:** `_spawn_gpu()` — background thread, retry 3x, 13 zonas
- **Bootstrap:** `startup_arch4.sh` — Docker + NVIDIA + GCS Fuse + pull golden + run
- **Auto-orquestra:** `industrial_main.py` — polling Firestore continuo (10s)
- **Shutdown:** idle 15min + after-job 5min + dead man 120min

## 3. Parametros de Render (OFICIAIS)
| Parametro | Valor | Onde |
|---|---|---|
| Template | `lana_comentario.mp4` | `agente_lana_orchestrator.py:700` |
| Guidance | 1.5 | `industrial_main.py:167` |
| Steps | 20 | `industrial_main.py:168` |
| DeepCache | ON | `industrial_main.py:169` |
| Seed | aleatorio | removido (nao passado) |
| Mascara | original (sem dilate/erode) | submodule `lipsync_pipeline.py` |
| GFPGAN | Lazy import + restore_video | submodule `lipsync_pipeline.py:266` |
| BasicSR | git master (compativel torchvision 0.20) | Golden Dockerfile |

## 4. Imagens Docker (Artifact Registry)
- **API:** `avatar-api:latest`
- **GPU:** `avatar-l4:v2.10-golden`
  - CUDA 12.1 + PyTorch 2.5.1
  - LatentSync via git submodule
  - basicSR + GFPGAN + facexlib
  - DeepCache do git

## 5. GCP
- **Projeto:** `brasili-ia-news`
- **Regiao:** `us-east1`
- **VM API SA:** `180096224219-compute@developer.gserviceaccount.com`
- **Firestore:** `avatar_jobs`
- **GCS Vault:** `gs://brasil-ai-avatars-vault`
- **GCS Weights:** `gs://lana-weights-universal` (GCS Fuse `/mnt/weights`)

## 6. Custos
| Recurso | Custo |
|---|---|
| VM e2-micro (24/7) | ~$6/mes |
| IP estatico | ~$3/mes |
| GPU L4 (sob demanda) | ~$0.70/h |
| Auto-shutdown | 15min idle / 5min after-job |

## 7. CI/CD
| YAML | Proposito |
|---|---|
| `cloudbuild-api.yaml` | Build + push API |
| `cloudbuild-l4-golden.yaml` | Build golden L4 |
| `cloudbuild-all.yaml` | Ambos (release) |

## 8. Rollback
```bash
git checkout -- latentsync/latentsync/pipelines/lipsync_pipeline.py  # submodule
git revert HEAD  # ultimo commit
```

## 9. Checklist Operacional
1. GPU rodando? `gcloud compute instances list --filter="name~lana-engine-"`
2. API online? `curl http://35.231.46.76:8080/health`
3. Video pronto? `gsutil ls gs://brasil-ai-avatars-vault/outputs/`
4. Custo? Desligar GPUs ociosas

---
*Status: v3.2.0 PRODUCAO — LatentSync + GFPGAN + basicSR fix. End-to-end funcional.*
