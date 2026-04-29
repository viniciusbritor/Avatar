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
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Importa o Orquestrador Industrial
from src.agente_lana_orchestrator import AgenteLanaOrchestrator
from .secrets_manager import get_secret

# ── Configuração ──────────────────────────────────────────────────────────────
API_SECRET_KEY = get_secret("API_SECRET_KEY", fallback="brasilai-avatar-2026")

# Gerenciador de Estado em Memória (Para o Cloud Run, o status real deve ser consultado via GCS/Logs)
# Mas para a sessão atual, mantemos este dicionário.
jobs_status: Dict[str, dict] = {}

app = FastAPI(
    title="Brasil AI — Avatar Industrial API",
    description="Orquestração Direta via Agno (Zero-Waste GPU Pipeline).",
    version="2.8.0",
)


class ProduceRequest(BaseModel):
    text: str


def _check_key(x_api_key: str):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="X-API-Key inválida.")


def run_orchestration_task(job_id: str, text: str):
    """Tarefa de fundo que executa o Agno Orchestrator."""
    global jobs_status
    orchestrator = AgenteLanaOrchestrator()
    
    try:
        jobs_status[job_id]["status"] = "running"
        jobs_status[job_id]["message"] = "Provisionando GPU L4 no GCP..."
        
        # O orquestrador já lida com: provisionamento, health check cego (SERVER_OK) e render
        result = orchestrator.produce_video_from_text(text, index=1, total=1)
        
        if result["status"] == "success":
            jobs_status[job_id]["status"] = "completed"
            jobs_status[job_id]["message"] = "Sucesso! Vídeo disponível no GCS."
            jobs_status[job_id]["video_path"] = result.get("video_path")
        else:
            jobs_status[job_id]["status"] = "failed"
            jobs_status[job_id]["message"] = f"Erro no Orquestrador: {result.get('message')}"
            
    except Exception as e:
        jobs_status[job_id]["status"] = "failed"
        jobs_status[job_id]["message"] = f"Erro Crítico: {str(e)}"
    
    finally:
        jobs_status[job_id]["completed_at"] = datetime.utcnow().isoformat()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "version": "2.8.0", "engine": "Agno-Maestro-V18"}


@app.post("/produce")
async def produce(request: ProduceRequest, background_tasks: BackgroundTasks, x_api_key: str = Header(...)):
    """Enfileira a produção de um avatar via Agno Orchestrator."""
    _check_key(x_api_key)

    if len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (mínimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    
    # Registra estado inicial
    jobs_status[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job enfileirado no Agno Orchestrator.",
        "text": request.text,
        "created_at": datetime.utcnow().isoformat(),
        "video_path": None,
        "completed_at": None
    }
    
    # Dispara a orquestração em background
    background_tasks.add_task(run_orchestration_task, job_id, request.text)

    return JSONResponse(content={
        "job_id": job_id,
        "status": "queued",
        "message": f"Job {job_id} enfileirado! Use GET /status/{job_id}.",
        "created_at": jobs_status[job_id]["created_at"]
    })


@app.get("/status/{job_id}")
def get_status(job_id: str, x_api_key: str = Header(...)):
    """Consulta o status do job de orquestração."""
    _check_key(x_api_key)

    job = jobs_status.get(job_id)
    if not job:
        # Se não estiver em memória (Cloud Run reciclado), o usuário deve olhar o bucket GCS
        raise HTTPException(
            status_code=404, 
            detail="Job não encontrado em memória. Verifique o bucket GCS para o resultado final."
        )

    return JSONResponse(content=job)


@app.get("/jobs")
def list_jobs(x_api_key: str = Header(...)):
    """Lista os últimos jobs da sessão atual."""
    _check_key(x_api_key)
    return JSONResponse(content={
        "total": len(jobs_status),
        "jobs": list(jobs_status.values())
    })
