# Dashboard Industrial — Brasil AI Avatar v3.2.1

**Status:** Produção ativa em VM e2-micro (IP fixo `35.231.46.76`)
**GPU:** L4 g2-standard-12 sob demanda, 13 zonas globais
**Last Update:** 2026-05-05 (Sessão opencode/deepseek)

---

## Componentes

| Componente | Local | Status |
|---|---|---|
| API | VM `lana-api` (us-east1-b, IP 35.231.46.76) | Ativa |
| GPU | `lana-engine-l4-*` (sob demanda) | Auto-spawn |
| Firestore | `avatar_jobs` | Ativo |
| GCS Vault | `gs://brasil-ai-avatars-vault` | Ativo |
| GCS Weights | `gs://lana-weights-universal` (GCS Fuse) | Ativo |

## Pipeline

1. POST /produce → TTS ElevenLabs → Firestore (queued)
2. GPU spawn (13 zonas) → startup_arch4.sh → docker pull golden image → docker cp código → container
3. GPU polling Firestore → LatentSync + GFPGAN → ffmpeg → upload GCS
4. Webhook → Firestore (completed) → sync_bridge.py download local

## Shutdown

| Camada | Tempo | Mecanismo |
|---|---|---|
| Idle GPU | 30 min | Sentinel HOST (systemd) |
| Container morto | 30 min | Sentinel HOST |
| Dead Man Switch | 90 min | `at` command |

## Custos

| Recurso | Custo mensal |
|---|---|
| VM e2-micro 24/7 | ~$6 |
| IP estático | $0 (VM ligada) |
| GPU L4 | ~$0.70/hora |

---
*Atualizado em 2026-05-05 — v3.2.1 com Sentinel HOST e docker cp para golden image.*
