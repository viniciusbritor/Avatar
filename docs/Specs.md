# Especificacoes Tecnicas Operacionais — Avatar v3.2.1 (PRODUCAO)

## 1. API (Cerebro)
- **Host:** VM e2-micro `lana-api` (us-east1-b)
- **IP Fixo:** `35.231.46.76`
- **Endpoints:**
    - `POST /produce`: Enfileira producao (TTS + Firestore + spawn GPU) — ~5s
    - `GET /status/{job_id}`: Consulta estado no Firestore
    - `GET /health`: Diagnostico da API
    - `POST /webhook/render-complete`: Callback da GPU
- **Entrypoint:** ADC nativo, sem gcloud auth manual
- **Workers:** 1 uvicorn (e2-micro: 2 vCPU, 1 GB RAM)

## 2. GPU (Motor L4)
- **Hardware:** `g2-standard-12` (NVIDIA L4, 22 GB VRAM)
- **Auto-orquestra:** `industrial_main.py` — polling Firestore continuo (10s)
- **Shutdown:** idle 15min + after-job 5min + dead man 120min

## 3. Pipeline de Render (v3.2.1)
| Parametro | Valor | Onde |
|---|---|---|
| Template | `lana_comentario.mp4` | `agente_lana_orchestrator.py:700` |
| Whisper | `small.pt` + projecao linear 768→384 | `inference.py` + `lipsync_pipeline.py` |
| Guidance | 2.5 | `industrial_main.py:167` |
| Steps | 20 | `industrial_main.py:168` |
| DeepCache | ON | `industrial_main.py:169` |
| Voz | Matilda (`XrExE9yKIg1WjnnlVkGX`) | `agente_lana_orchestrator.py:27` |
| GFPGAN | ON (lazy import) | submodule `lipsync_pipeline.py:266` |
| Seed | aleatorio | removido |

## 4. Modelos no GCS Bucket
| Modelo | Path | Tamanho |
|---|---|---|
| LatentSync UNet | `gs://lana-weights-universal/checkpoints/latentsync_unet.pt` | 3.2 GB |
| Whisper small | `gs://lana-weights-universal/checkpoints/whisper/small.pt` | 461 MB |
| Whisper tiny | `gs://lana-weights-universal/checkpoints/whisper/tiny.pt` | 72 MB |
| GFPGAN | `gs://lana-weights-universal/checkpoints/gfpgan/GFPGANv1.4.pth` | 332 MB |

## 5. Imagens Docker (Artifact Registry)
- **API:** `avatar-api:latest`
- **GPU:** `avatar-l4:v2.10-golden`
  - CUDA 12.1 + PyTorch 2.5.1
  - LatentSync via git submodule (`bytedance/LatentSync`)
  - basicSR (git master) + GFPGAN + facexlib
  - Mirror GCP do Ubuntu (apt)

## 6. GCP
- **Projeto:** `brasili-ia-news`
- **Regiao:** `us-east1`
- **Firestore:** `avatar_jobs`
- **GCS Vault:** `gs://brasil-ai-avatars-vault`
- **GCS Weights:** `gs://lana-weights-universal` (GCS Fuse `/mnt/weights`)

## 7. Custos
| Recurso | Custo |
|---|---|
| VM e2-micro (24/7) | ~$6/mes |
| IP estatico | ~$3/mes |
| GPU L4 (sob demanda) | ~$0.70/h |

## 8. CI/CD
| YAML | Proposito |
|---|---|
| `cloudbuild-api.yaml` | Build + push API |
| `cloudbuild-l4-golden.yaml` | Build golden L4 |
| `cloudbuild-all.yaml` | Ambos (release) |

## 9. Branches
| Branch | Status |
|---|---|
| `master` | **Producao v3.2.1** |
| `sincronia` | Testes A-D |
| `linear-projection` | Merged → master |
| `checkpoint-768` | Experimental |

---
*Status: v3.2.1 PRODUCAO — small.pt + projecao 768→384 + guidance 2.5 + Matilda + GFPGAN.*
