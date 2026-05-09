# Brasil AI — Avatar API
## Guia de Deploy (VM e2-micro IP fixo — v4.3)

### Estrutura

```
Avatar/
├── src/                        # Pipeline original
│   ├── agente_lana_orchestrator.py
│   ├── produce_requested_videos.py
│   ├── industrial_main.py
│   └── secrets_manager.py
├── infra/
│   ├── startup_arch4.sh        # Boot script GPU L4 (git clone + nvidia-ctk)
│   └── startup-e2-micro.sh     # Boot script VM API
├── api/                        # API layer
│   ├── Dockerfile              # Container imagem API
│   ├── requirements.txt
│   ├── main.py                 # FastAPI server (v3.2.2)
│   ├── secrets_manager.py      # Consulta GCP Secret Manager + fallback
│   └── cloud_engine.py         # Subclasse engine (Linux)
└── outputs/                    # Saída local
```

### Cofre de Segredos (GCP Secret Manager)

Credenciais de APIs externas (ElevenLabs, Gemini) são obtidas em runtime via `secrets_manager.py` consultando o GCP Secret Manager. Tokens internos (ex: `API_SECRET_KEY`) possuem fallback em código.

| Secret | Finalidade |
|--------|-----------|
| `API_SECRET_KEY` | Token interno HTTP — Cérebro ↔ Motor |
| `ELEVEN_LABS_API_KEY` | ElevenLabs TTS |
| `ELEVEN_VOICE_ID` | Voz Matilda (pt-BR) |
| `GEMINI_API_KEY` | Google Gemini (Maestro) |

**CI/CD Authentication:** GitHub Actions usa Workload Identity Federation (OIDC) — sem chaves exportadas. A Service Account `github-actions-sa@brasili-ia-news.iam.gserviceaccount.com` tem permissões granulares (least-privilege) vinculadas ao repositório `viniciusbritor/Avatar`.

**Backup offline:** `gs://brasil-ai-avatars-vault/brasil_ai.db` (SQLite com todas as chaves do ecossistema YouTube). Não usado em runtime.

---

### 1. Deploy (Cloud Build → Artifact Registry → Update Manual)

O CI/CD faz build + push automaticamente. O deploy na VM é sempre manual.

```bash
# 1. Commit e push no GitHub → CI/CD trigga Cloud Build
git add -A && git commit -m "..." && git push origin master

# 2. GitHub Actions → gcloud builds submit → imagem no Artifact Registry

# 3. Atualizar a VM manualmente via SSH
gcloud compute ssh lana-api --zone=us-east1-c --tunnel-through-iap
sudo lana-update.sh
```

O script `lana-update.sh` puxa a imagem do Artifact Registry (fonte única, sem cache local), faz prune de imagens velhas, reinicia o container, e verifica o `/health`. Se o pull falhar, o container atual continua rodando.

A VM está em **us-east1-c**, roda **e2-micro** com disco **30 GB pd-standard** e IP fixo regional `35.231.46.76`. Base image: **`ubuntu-2204-lts`** (`ubuntu-os-cloud`). Deploy manual via `sudo lana-update.sh` (sem cron). O container usa `--restart unless-stopped` e `--pull always` — sempre puxa do Artifact Registry.

### 2. Uso da API

**Solicitar Avatar:**
```bash
curl -X POST http://35.231.46.76:8080/produce \
  -H "X-API-Key: brasilai-avatar-2026" \
  -H "Content-Type: application/json" \
  -d '{"text": "Eu sou a Cris do Brasil AI, isso e um teste."}'
```

**Resposta:**
```json
{
  "job_id": "a2cdc85b",
  "status": "queued",
  "message": "Job a2cdc85b enfileirado. GPU sera iniciada.",
  "created_at": "2026-05-05T19:03:17-03:00"
}
```

**Acompanhar Progresso:**
```bash
curl http://35.231.46.76:8080/status/a2cdc85b \
  -H "X-API-Key: brasilai-avatar-2026"
```

**Health Check:**
```bash
curl http://35.231.46.76:8080/health
```

### 3. Download do Vídeo (Entrega Local)

Após o job atingir `status: completed`, o vídeo está no bucket GCS e deve ser baixado para a máquina local.

**Método Automático (recomendado):**
```bash
python src/sync_bridge.py --once
```
Baixa todos os jobs `completed` ainda não baixados para a pasta `sucesso/`.

**Método Manual:**
```bash
gsutil cp gs://brasil-ai-avatars-vault/outputs/final_<JOB_ID>.mp4 sucesso/
```

**Caminho local de saída:** `C:\Users\vinic\workspace_antigravity\Avatar\sucesso\`
