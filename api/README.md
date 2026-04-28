# Brasil AI — Avatar API
## Guia de Deploy (Cloud Run)

### Estrutura (Paralela — Pipeline Original Intacto)

```
Avatar/
├── src/                        # ✅ Pipeline original — NÃO MODIFICADO
│   ├── agente_lana_orchestrator.py
│   ├── produce_requested_videos.py   # Ainda funciona localmente
│   ├── industrial_main.py
│   └── secrets_manager.py
├── infra/
│   └── startup_arch4.sh        # Shared com API e pipeline local
├── api/                        # 🆕 Nova camada de API (Cloud Run)
│   ├── Dockerfile              # Container com gcloud SDK
│   ├── requirements.txt
│   ├── main.py                 # FastAPI server
│   └── cloud_engine.py        # Subclasse do engine (path cloud)
└── outputs/                    # Saída local (ainda funciona)
```

### Rollback Seguro
Caso algo dê errado, volte para o estado blindado:
```bash
git checkout v1.0-BLINDADA-FUNCIONAL
```
O pipeline local (produce_requested_videos.py) nunca foi modificado.

---

### 1. Pré-requisito: Service Account GCP

Crie uma SA com permissões:
- `Compute Admin`
- `Storage Admin`
- `Artifact Registry Writer`
- `Secret Manager Secret Accessor`

```bash
gcloud iam service-accounts create avatar-api-sa \
  --project brasili-ia-news \
  --display-name "Avatar API Service Account"

# Dar permissões
for role in roles/compute.admin roles/storage.admin roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding brasili-ia-news \
    --member="serviceAccount:avatar-api-sa@brasili-ia-news.iam.gserviceaccount.com" \
    --role="$role"
done
```

### 2. Deploy

```bash
# Do diretório raiz do projeto Avatar/
gcloud run deploy avatar-api \
  --project brasili-ia-news \
  --region us-east1 \
  --source . \
  --dockerfile api/Dockerfile \
  --service-account avatar-api-sa@brasili-ia-news.iam.gserviceaccount.com \
  --set-env-vars "API_SECRET_KEY=SEU_TOKEN_AQUI,STARTUP_SCRIPT_PATH=/app/infra/startup_arch4.sh" \
  --timeout 3600 \
  --memory 2Gi \
  --cpu 2 \
  --no-allow-unauthenticated
```

### 3. Uso da API

**Solicitar Avatar:**
```bash
curl -X POST https://avatar-api-xxx.run.app/produce \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"text": "Eu sou a Cris do Brasil AI, isso é um teste."}'
```

**Resposta:**
```json
{
  "job_id": "a2cdc85b",
  "status": "queued",
  "message": "Job enfileirado! Use GET /status/a2cdc85b para acompanhar.",
  "created_at": "2026-04-28T22:30:00Z"
}
```

**Acompanhar Progresso:**
```bash
curl https://avatar-api-xxx.run.app/status/a2cdc85b \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Interface Visual (Swagger UI):**
Abra no navegador: `https://avatar-api-xxx.run.app/docs`

---

### 4. Configuração de Secrets (Phase 2C)
O `secrets_manager.py` já detecta automaticamente Cloud Run via `K_SERVICE`.
Basta subir o `brasil_ai.db` para o Bucket GCS:

```bash
gsutil cp src/brasil_ai.db gs://brasil-ai-avatars-vault/brasil_ai.db
```
