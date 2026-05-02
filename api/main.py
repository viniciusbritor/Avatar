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


@app.post("/produce")
async def produce(request: Request, payload: ProduceRequest, x_api_key: str = Header(...)):
    """Enfileira producao: gera audio, salva Firestore, inicia GPU L4."""
    _check_key(x_api_key)

    if not db:
        raise HTTPException(status_code=500, detail="Firestore indisponivel.")

    if len(payload.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (minimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    webhook_url = f"{str(request.base_url).rstrip('/')}/webhook/render-complete"

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
        "audio_url": f"gs://{orchestrator.engine.bucket_name}/{audio_gcs.split('/')[-2]}/{audio_gcs.split('/')[-1]}" if hasattr(orchestrator.engine, 'bucket_name') else audio_gcs,
        "webhook_url": webhook_url,
        "created_at": datetime.now(BRT).isoformat(),
        "video_path": None,
        "completed_at": None,
        "message": "Enfileirado. GPU L4 processara em breve."
    }

    JOBS_COLLECTION.document(job_id).set(job_data)

    try:
        orchestrator.engine.ensure_instance_ready(
            progress_callback=lambda m: print(f"[ORQ] {m}")
        )
    except Exception as e:
        print(f"[ORQ] Aviso: GPU nao iniciada: {e}")
        JOBS_COLLECTION.document(job_id).update({
            "message": f"GPU pendente: {str(e)[:100]}"
        })

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": f"Job {job_id} enfileirado. GPU L4 sera iniciada.",
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
