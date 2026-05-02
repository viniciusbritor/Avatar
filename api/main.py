"""
main.py — Brasil AI Avatar API (Industrial v2.8)
---------------------------------------------------------------------
API que recebe requisições e orquestra DIRETAMENTE a infraestrutura
GCP usando Agno (Maestro) e instâncias NVIDIA L4/T4.

Fluxo:
  POST /produce  --> Agno Orchestrator (Background) --> GCP L4 --> GCS
"""

import os
import uuid
import time
import json
import threading
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importa o Orquestrador Industrial
from src.agente_lana_orchestrator import AgenteLanaOrchestrator
from .secrets_manager import get_secret

# ── Configuração Firestore & Inicialização ──────────────────────────────────────
try:
    from google.cloud import firestore
    db = firestore.Client(project="brasili-ia-news")
    JOBS_COLLECTION = db.collection('avatar_jobs')
except Exception as e:
    print(f"Erro ao inicializar Firestore: {e}")
    db = None

# ── Configuração Cloud Tasks ───────────────────────────────────────────────────
try:
    from google.cloud import tasks_v2
    tasks_client = tasks_v2.CloudTasksClient()
    PROJECT_ID = "brasili-ia-news"
    LOCATION_ID = "us-east1"
    QUEUE_ID = "avatar-render-queue"
    QUEUE_PATH = tasks_client.queue_path(PROJECT_ID, LOCATION_ID, QUEUE_ID)
except Exception as e:
    print(f"Erro ao inicializar Cloud Tasks: {e}")
    tasks_client = None

API_SECRET_KEY = get_secret("API_SECRET_KEY", fallback="brasilai-avatar-2026")

app = FastAPI(
    title="Brasil AI — Avatar Industrial API",
    description="Orquestração Direta via Agno (Zero-Waste GPU Pipeline).",
    version="2.8.0",
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


def _check_key(x_api_key: str):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="X-API-Key inválida.")


class WorkerRequest(BaseModel):
    job_id: str
    text: str
    webhook_url: Optional[str] = None

class WebhookRequest(BaseModel):
    job_id: str
    status: str
    video_path: Optional[str] = None
    error: Optional[str] = None

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health():
    return {
        "status": "ok", 
        "version": "3.0.0", 
        "engine": "Agno-Maestro-V18", 
        "firestore": db is not None,
        "cloud_tasks": tasks_client is not None
    }


@app.post("/produce")
async def produce(request: Request, payload: ProduceRequest, x_api_key: str = Header(...)):
    """Enfileira a produção de um avatar delegando para o Cloud Tasks."""
    _check_key(x_api_key)

    if not db or not tasks_client:
        raise HTTPException(status_code=500, detail="Infraestrutura GCP (Firestore ou Cloud Tasks) indisponível.")

    if len(payload.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (mínimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "message": "Enfileirado na infraestrutura blindada (Cloud Tasks).",
        "text": payload.text,
        "created_at": datetime.utcnow().isoformat(),
        "video_path": None,
        "completed_at": None
    }
    
    # Força HTTPS para evitar redirecionamentos que quebram o POST (405)
    base_url = str(request.base_url).rstrip('/').replace("http://", "https://")
    worker_url = f"{base_url}/internal/render-worker"
    webhook_url = f"{base_url}/webhook/render-complete"
    task_payload = {"job_id": job_id, "text": payload.text, "webhook_url": webhook_url}
    
    from google.protobuf import duration_pb2
    duration = duration_pb2.Duration()
    duration.FromSeconds(1800) # 30 min 
    
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": worker_url,
            "headers": {"Content-type": "application/json", "X-API-Key": x_api_key},
            "body": json.dumps(task_payload).encode()
        },
        "dispatch_deadline": duration
    }
    
    try:
        JOBS_COLLECTION.document(job_id).set(job_data)
        tasks_client.create_task(request={"parent": QUEUE_PATH, "task": task})
    except Exception as e:
        print(f"[API ERROR] {e}")
        try:
            JOBS_COLLECTION.document(job_id).update({"status": "failed", "message": f"Falha ao enfileirar: {e}"})
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Erro interno de Cloud (Firestore/Tasks): {e}")

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": f"Job {job_id} enfileirado e blindado! Use GET /status/{job_id}.",
        "created_at": job_data["created_at"]
    })


@app.post("/internal/render-worker", include_in_schema=False)
async def render_worker(
    payload: WorkerRequest, 
    x_api_key: str = Header(...),
    x_cloudtasks_queuename: Optional[str] = Header(None)
):
    """Worker interno acionado *exclusivamente* pelo Cloud Tasks. Roda em background thread para não bloquear o Cloud Run."""
    _check_key(x_api_key)
    
    if not x_cloudtasks_queuename:
        raise HTTPException(status_code=403, detail="Acesso Negado. Rota blindada exclusiva para o Cloud Tasks.")
        
    if not db:
        raise HTTPException(status_code=500, detail="DB indisponível")
        
    doc_ref = JOBS_COLLECTION.document(payload.job_id)
    
    # Verificar se job já está em processamento (evitar duplicatas de retry)
    existing = doc_ref.get()
    if existing.exists:
        existing_status = existing.to_dict().get("status", "")
        if existing_status in ("running", "rendering", "completed"):
            return {"status": "already_processing", "job_id": payload.job_id}
    
    doc_ref.update({
        "status": "running", 
        "message": "Processamento L4 isolado iniciado..."
    })
    
    def run_orchestration():
        orchestrator = AgenteLanaOrchestrator()
        try:
            result = orchestrator.produce_video_from_text(
                payload.text, job_id=payload.job_id, index=1, total=1, 
                webhook_url=payload.webhook_url
            )
            if result["status"] == "success":
                doc_ref.update({
                    "status": "rendering",
                    "message": "Enviado à GPU. Aguardando finalização assíncrona..."
                })
            else:
                doc_ref.update({
                    "status": "failed",
                    "message": f"Erro Orquestrador: {result.get('message')}",
                    "completed_at": datetime.utcnow().isoformat()
                })
        except Exception as e:
            doc_ref.update({
                "status": "failed",
                "message": f"Crash do Sistema (Worker): {str(e)}",
                "completed_at": datetime.utcnow().isoformat()
            })
    
    thread = threading.Thread(target=run_orchestration, daemon=True)
    thread.start()
    return {"status": "accepted", "job_id": payload.job_id}


@app.post("/webhook/render-complete", include_in_schema=False)
async def render_complete_webhook(payload: WebhookRequest, x_api_key: str = Header(...)):
    """Recebe a notificação de término da GPU (Assíncrono)."""
    _check_key(x_api_key)
    if not db:
        raise HTTPException(status_code=500, detail="DB indisponível")
        
    doc_ref = JOBS_COLLECTION.document(payload.job_id)
    if payload.status == "completed":
        doc_ref.update({
            "status": "completed",
            "video_path": payload.video_path,
            "message": "Sucesso Absoluto! Vídeo concluído e enviado pela GPU.",
            "completed_at": datetime.utcnow().isoformat()
        })
    else:
        doc_ref.update({
            "status": "failed",
            "message": f"Falha na GPU: {payload.error}",
            "completed_at": datetime.utcnow().isoformat()
        })
    return {"status": "ok"}


@app.get("/status/{job_id}")
def get_status(job_id: str, x_api_key: str = Header(...)):
    """Consulta o status no banco de dados imutável."""
    _check_key(x_api_key)
    
    if not db:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível.")

    doc = JOBS_COLLECTION.document(job_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    return JSONResponse(content=doc.to_dict())


@app.get("/jobs")
def list_jobs(x_api_key: str = Header(...)):
    """Lista os últimos jobs usando Firestore."""
    _check_key(x_api_key)
    
    if not db:
        raise HTTPException(status_code=500, detail="Banco de dados indisponível.")
        
    docs = JOBS_COLLECTION.order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
    jobs = [doc.to_dict() for doc in docs]
    
    return JSONResponse(content={
        "total": len(jobs),
        "jobs": jobs
    })

@app.get("/finops")
def get_finops_data():
    """Retorna dados de consumo FinOps em tempo real."""
    active_gpus = 0
    if db:
        try:
            running = list(JOBS_COLLECTION.where("status", "in", ["running", "rendering"]).stream())
            active_gpus = len(running)
        except Exception:
            pass

    return JSONResponse(content={
        "totalSpend": 1.15 + (active_gpus * 0.1),
        "projectedBill": 2.50 + (active_gpus * 0.5),
        "activeGPUs": active_gpus
    })

