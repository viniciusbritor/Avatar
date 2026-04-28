"""
main.py — Brasil AI Avatar API (Cloud Run)
-------------------------------------------
Servidor FastAPI que expõe o pipeline de criação de avatares como
uma API REST. Substitui o produce_requested_videos.py manual.

Endpoints:
  POST  /produce          → Solicita criação de um avatar
  GET   /status/{job_id}  → Consulta o progresso de um job
  GET   /jobs             → Lista todos os jobs da sessão
  GET   /health           → Health check do servidor

Autenticação: Bearer token via env var API_SECRET_KEY.
"""

import os
import sys
import uuid
import threading
import traceback
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Adicionar src/ ao path ────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from secrets_manager import get_secret
from cloud_engine import CloudLanaEngine
from agente_lana_orchestrator import AgenteLanaOrchestrator

# ── Configuração ──────────────────────────────────────────────────────────────
API_SECRET_KEY = os.getenv("API_SECRET_KEY", get_secret("AVATAR_API_KEY", fallback="brasil-ai-2025"))

app = FastAPI(
    title="Brasil AI — Avatar API",
    description="API soberana de criação de avatares com LatentSync + ElevenLabs Sarah.",
    version="2.0.0",
)

security = HTTPBearer()

# ── Armazenamento em memória de Jobs ─────────────────────────────────────────
# Para escalabilidade futura, substituir por Firestore/Redis.
jobs: dict[str, dict] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────
class ProduceRequest(BaseModel):
    text: str
    force_new_gpu: bool = False


class ProduceResponse(BaseModel):
    job_id: str
    status: str
    message: str
    created_at: str


# ── Auth ──────────────────────────────────────────────────────────────────────
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return credentials


# ── Worker (Roda em Thread Separada) ─────────────────────────────────────────
def _run_production(job_id: str, text: str, force_gpu: bool):
    """Executa o pipeline completo em background. Atualiza jobs[job_id]."""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Inicializando orquestrador..."

        # Instancia o orquestrador com o engine adaptado para Cloud Run
        orchestrator = AgenteLanaOrchestrator()
        orchestrator.engine = CloudLanaEngine()  # Substituir engine local pelo cloud

        def progress_cb(msg):
            jobs[job_id]["message"] = msg

        jobs[job_id]["message"] = "Provisionando GPU L4 no GCP..."
        result = orchestrator.produce_video_from_text(
            text,
            index=1,
            total=1,
            force_gpu=force_gpu
        )

        if result["status"] == "success":
            jobs[job_id].update({
                "status": "completed",
                "message": "Vídeo entregue com sucesso!",
                "video_path": result.get("video_path"),
                "completed_at": datetime.utcnow().isoformat(),
            })
        else:
            jobs[job_id].update({
                "status": "failed",
                "message": result.get("message", "Erro desconhecido"),
            })

    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "message": f"Erro crítico: {str(e)[:300]}",
            "traceback": traceback.format_exc()[:1000],
        })


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/produce", response_model=ProduceResponse, summary="Solicita criação de um avatar")
def produce(request: ProduceRequest, token=Depends(verify_token)):
    """
    Inicia a produção de um vídeo avatar em background.
    Retorna imediatamente com um `job_id` para acompanhar o progresso.
    """
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (mínimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job enfileirado. Aguardando worker...",
        "text": request.text,
        "created_at": datetime.utcnow().isoformat(),
        "video_path": None,
        "completed_at": None,
    }

    # Dispara em background para não bloquear a resposta HTTP
    thread = threading.Thread(
        target=_run_production,
        args=(job_id, request.text, request.force_new_gpu),
        daemon=True
    )
    thread.start()

    return ProduceResponse(
        job_id=job_id,
        status="queued",
        message=f"Job {job_id} enfileirado! Use GET /status/{job_id} para acompanhar.",
        created_at=jobs[job_id]["created_at"],
    )


@app.get("/status/{job_id}", summary="Consulta o status de um job")
def get_status(job_id: str, token=Depends(verify_token)):
    """Retorna o estado atual de um job de produção."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' não encontrado.")
    return JSONResponse(content=job)


@app.get("/jobs", summary="Lista todos os jobs da sessão")
def list_jobs(token=Depends(verify_token)):
    """Retorna todos os jobs processados desde o último deploy."""
    return JSONResponse(content={"total": len(jobs), "jobs": list(jobs.values())})


@app.get("/health", include_in_schema=False)
def health():
    """Health check para o Cloud Run."""
    return {"status": "ok", "version": "2.0.0", "service": "brasil-ai-avatar-api"}
