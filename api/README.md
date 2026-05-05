# Brasil AI — Avatar API
## Guia de Deploy (VM e2-micro IP fixo — v3.2.1)

### Estrutura

```
Avatar/
├── src/                        # Pipeline original
│   ├── agente_lana_orchestrator.py
│   ├── produce_requested_videos.py
│   ├── industrial_main.py
│   └── secrets_manager.py
├── infra/
│   ├── startup_arch4.sh        # Boot script GPU L4
│   └── startup-e2-micro.sh     # Boot script VM API
├── api/                        # API layer
│   ├── Dockerfile              # Container imagem API
│   ├── requirements.txt
│   ├── main.py                 # FastAPI server (v3.2.1)
│   └── cloud_engine.py         # Subclasse engine (Linux)
└── outputs/                    # Saída local
```

### Rollback Seguro
Caso algo dê errado, volte para o estado blindado:
```bash
git checkout v1.0-BLINDADA-FUNCIONAL
```

---

### 1. Deploy (Cloud Build → Artifact Registry → VM cron auto-update)

O deploy é **totalmente automatizado**:

```bash
# 1. Commit e push no GitHub
git add -A && git commit -m "..." && git push origin master

# 2. Cloud Build gera a imagem e faz push para Artifact Registry
gcloud builds submit --project brasili-ia-news --region us-east1 --config cloudbuild-api.yaml .

# 3. A VM lana-api (35.231.46.76) puxa a nova imagem via cron a cada 5 min
#    Script: /usr/local/bin/lana-auto-update.sh
```

A VM está em **us-east1-b**, roda **e2-micro** com IP fixo. O container usa `--restart unless-stopped` — sobrevive a restart da VM.

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
