"""
main.py — Brasil AI Avatar API (v3.2.0 — VM e2-micro)
---------------------------------------------------------------------
API leve rodando em VM fixa. Sem Cloud Run, sem Cloud Tasks, sem SIGHUP.
Fluxo:
  POST /produce → TTS → Firestore (queued) → inicia GPU L4 → retorna
  GPU L4 → polling Firestore → render → webhook → Firestore (completed)
"""

import os
import uuid
import subprocess
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agente_lana_orchestrator import AgenteLanaOrchestrator
from .secrets_manager import get_secret

BRT = timezone(timedelta(hours=-3))

try:
    from google.cloud import firestore
    db = firestore.Client(project="brasili-ia-news")
    JOBS_COLLECTION = db.collection('avatar_jobs')
except Exception as e:
    print(f"Firestore indisponivel: {e}")
    db = None

API_SECRET_KEY = get_secret("API_SECRET_KEY", fallback="brasilai-avatar-2026")

app = FastAPI(
    title="Brasil AI — Avatar API",
    description="Orquestracao Zero-Waste via VM e2-micro + GPU L4 sob demanda.",
    version="3.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProduceRequest(BaseModel):
    text: str


class WebhookRequest(BaseModel):
    job_id: str
    status: str
    video_path: Optional[str] = None
    error: Optional[str] = None


def _check_key(x_api_key: str):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="X-API-Key invalida.")


@app.get("/health", include_in_schema=False)
def health():
    return {
        "status": "ok",
        "version": "3.2.0",
        "engine": "VM-e2-micro",
        "firestore": db is not None
    }


def _spawn_gpu():
    """Background: liga ou cria VM L4 com retry 3x. Sem SSH."""
    L4_MACHINE = "g2-standard-12"
    IMAGE_FAMILY = "common-cu129-ubuntu-2204-nvidia-580"
    IMAGE_PROJECT = "deeplearning-platform-release"
    ZONES = ["us-east1-c", "us-west4-a", "us-east1-d", "us-east4-a", "us-west1-a",
             "us-central1-a", "us-east5-a", "us-south1-a", "europe-west4-a",
             "europe-west1-b", "europe-west6-b", "asia-east1-a",
             "northamerica-northeast1-b"]
    PROJECT = "brasili-ia-news"

    import uuid as _uuid
    import time as _time

    for attempt in range(3):
        try:
            existing = subprocess.run(
                ["gcloud", "compute", "instances", "list",
                 "--filter=name~lana-engine- AND status=RUNNING",
                 "--format=json", "--project", PROJECT, "--quiet", "--verbosity=none"],
                capture_output=True, text=True, timeout=90
            )
            if existing.returncode == 0 and existing.stdout.strip():
                import json as _json
                instances = _json.loads(existing.stdout)
                if instances:
                    inst = sorted(instances, key=lambda x: x['name'], reverse=True)[0]
                    name, zone = inst['name'], inst['zone'].split('/')[-1]
                    print(f"[SPAWN] GPU ja ativa: {name} em {zone}")
                    return

            for zone in ZONES:
                name = f"lana-engine-l4-{int(_time.time())}-{_uuid.uuid4().hex[:4]}"
                print(f"[SPAWN] Tentativa {attempt+1}/3 — Criando {name} em {zone}...")
                res = subprocess.run(
                    ["gcloud", "compute", "instances", "create", name,
                     "--project", PROJECT, "--zone", zone,
                     f"--machine-type={L4_MACHINE}",
                     f"--image-family={IMAGE_FAMILY}",
                     f"--image-project={IMAGE_PROJECT}",
                     "--accelerator=count=1,type=nvidia-l4",
                     "--boot-disk-size=100GB",
                     "--provisioning-model=STANDARD",
                     "--maintenance-policy=TERMINATE",
                     "--metadata-from-file=startup-script=/app/infra/boot/startup_arch4.sh",
                     "--scopes=cloud-platform", "--quiet", "--verbosity=none"],
                    capture_output=True, text=True, timeout=120
                )
                if res.returncode == 0:
                    print(f"[SPAWN] GPU criada: {name} em {zone}")
                    return
                err = (res.stderr or "")[:200]
                if "Quota" in err or "GPUS_ALL_REGIONS" in err:
                    print(f"[SPAWN] Cota cheia em {zone}, tentando proxima zona...")
                    continue
                if "stockout" in err.lower() or "resource" in err.lower() or "ZONE_RESOURCE_POOL_EXHAUSTED" in err:
                    continue
                print(f"[SPAWN] Erro em {zone}: {err}")
        except Exception as e:
            print(f"[SPAWN] Erro tentativa {attempt+1}: {e}")
        if attempt < 2:
            _time.sleep(30)
    print("[SPAWN] GPU L4 nao encontrada apos 3 tentativas.")


@app.post("/produce")
async def produce(request: Request, payload: ProduceRequest, x_api_key: str = Header(...)):
    """Enfileira producao: gera audio, salva Firestore, dispara GPU L4."""
    _check_key(x_api_key)

    if not db:
        raise HTTPException(status_code=500, detail="Firestore indisponivel.")

    if len(payload.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (minimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    webhook_url = "http://35.231.46.76:8080/webhook/render-complete"

    orchestrator = AgenteLanaOrchestrator()

    try:
        audio_local = orchestrator.generate_audio_local(payload.text)
        audio_gcs = orchestrator.engine.upload_assets(audio_local, job_id=job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha no TTS: {e}")

    job_data = {
        "job_id": job_id,
        "status": "queued",
        "text": payload.text,
        "audio_url": f"gs://brasil-ai-avatars-vault/temp/{os.path.basename(audio_local)}",
        "webhook_url": webhook_url,
        "created_at": datetime.now(BRT).isoformat(),
        "video_path": None,
        "completed_at": None,
        "message": "Enfileirado. GPU L4 iniciando..."
    }

    JOBS_COLLECTION.document(job_id).set(job_data)

    threading.Thread(target=_spawn_gpu, daemon=True).start()

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": f"Job {job_id} enfileirado. GPU sera iniciada.",
        "created_at": job_data["created_at"]
    })


@app.post("/webhook/render-complete", include_in_schema=False)
async def render_complete_webhook(payload: WebhookRequest, x_api_key: str = Header(...)):
    """Recebe notificacao de termino da GPU."""
    _check_key(x_api_key)
    if not db:
        raise HTTPException(status_code=500, detail="DB indisponivel")

    doc_ref = JOBS_COLLECTION.document(payload.job_id)
    if payload.status == "completed":
        doc_ref.update({
            "status": "completed",
            "video_path": payload.video_path,
            "message": "Video concluido pela GPU.",
            "completed_at": datetime.now(BRT).isoformat()
        })
    else:
        doc_ref.update({
            "status": "failed",
            "message": f"Falha na GPU: {payload.error}",
            "completed_at": datetime.now(BRT).isoformat()
        })
    return {"status": "ok"}


@app.get("/status/{job_id}")
def get_status(job_id: str, x_api_key: str = Header(...)):
    """Consulta status no Firestore."""
    _check_key(x_api_key)
    if not db:
        raise HTTPException(status_code=500, detail="Firestore indisponivel.")

    doc = JOBS_COLLECTION.document(job_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Job nao encontrado.")
    return JSONResponse(content=doc.to_dict())


@app.get("/jobs")
def list_jobs(x_api_key: str = Header(...)):
    """Lista ultimos jobs."""
    _check_key(x_api_key)
    if not db:
        raise HTTPException(status_code=500, detail="Firestore indisponivel.")

    docs = JOBS_COLLECTION.order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
    jobs = [doc.to_dict() for doc in docs]
    return JSONResponse(content={"total": len(jobs), "jobs": jobs})
