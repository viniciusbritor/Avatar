"""
main.py — Brasil AI Avatar API (Cloud Run — GitHub Actions Trigger)
---------------------------------------------------------------------
API leve que recebe requisições e dispara o pipeline via GitHub Actions.
Não roda nenhum subprocess local. Zero compatibilidade Linux/Windows.

Fluxo:
  POST /produce  →  GitHub workflow_dispatch  →  Runner Linux  →  GCS
  GET  /status/{run_id}  →  GitHub Actions API  →  status do workflow
"""

import os
import uuid
import requests
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .secrets_manager import get_secret

# ── Configuração ──────────────────────────────────────────────────────────────
API_SECRET_KEY  = get_secret("API_SECRET_KEY", fallback="brasilai-avatar-2026")
GITHUB_TOKEN    = get_secret("GITHUB_TOKEN", fallback="")
GITHUB_REPO     = get_secret("GITHUB_REPO", fallback="viniciusbritor/Avatar")
GITHUB_WORKFLOW = get_secret("GITHUB_WORKFLOW", fallback="produce_avatar.yml")
GITHUB_BRANCH   = get_secret("GITHUB_BRANCH", fallback="master")

GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}"

app = FastAPI(
    title="Brasil AI — Avatar API",
    description="Dispara o pipeline de avatar via GitHub Actions.",
    version="3.0.0",
)


class ProduceRequest(BaseModel):
    text: str


def _check_key(x_api_key: str):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="X-API-Key inválida.")


def _trigger_github(text: str, job_id: str) -> dict:
    """Dispara o workflow no GitHub via workflow_dispatch."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN não configurado.")

    payload = {
        "ref": GITHUB_BRANCH,
        "inputs": {
            "text": text,
            "job_id": job_id
        }
    }
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    resp = requests.post(f"{GITHUB_API}/dispatches", json=payload, headers=headers, timeout=15)

    if resp.status_code not in (200, 204):
        raise HTTPException(
            status_code=502,
            detail=f"GitHub recusou o dispatch: {resp.status_code} — {resp.text[:200]}"
        )
    return {"dispatched": True}


def _get_latest_run(job_id: str) -> dict:
    """Busca o último run do workflow no GitHub."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN não configurado.")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/runs",
        headers=headers,
        params={"per_page": 10},
        timeout=15
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar GitHub: {resp.status_code}")

    runs = resp.json().get("workflow_runs", [])
    # Tenta encontrar o run com o job_id no nome
    for run in runs:
        if job_id in (run.get("display_title", "") + run.get("name", "") + str(run.get("id", ""))):
            return run
    # Retorna o mais recente se não encontrar
    return runs[0] if runs else {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "version": "3.0.0", "engine": "github-actions"}


@app.post("/produce")
def produce(request: ProduceRequest, x_api_key: str = Header(...)):
    """Enfileira a produção de um avatar via GitHub Actions."""
    _check_key(x_api_key)

    if len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Texto muito curto (mínimo 5 caracteres).")

    job_id = str(uuid.uuid4())[:8]
    _trigger_github(request.text, job_id)

    return JSONResponse(content={
        "job_id": job_id,
        "status": "triggered",
        "message": f"Pipeline disparado no GitHub Actions. Acompanhe em: https://github.com/{GITHUB_REPO}/actions",
        "github_actions_url": f"https://github.com/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}",
        "created_at": datetime.utcnow().isoformat()
    })


@app.get("/status/{job_id}")
def get_status(job_id: str, x_api_key: str = Header(...)):
    """Consulta o status do último run do workflow."""
    _check_key(x_api_key)

    run = _get_latest_run(job_id)
    if not run:
        raise HTTPException(status_code=404, detail="Nenhum run encontrado.")

    status_map = {
        "queued": "queued",
        "in_progress": "running",
        "completed": run.get("conclusion", "completed")
    }
    status = status_map.get(run.get("status", ""), run.get("status", "unknown"))

    return JSONResponse(content={
        "job_id": job_id,
        "github_run_id": run.get("id"),
        "status": status,
        "conclusion": run.get("conclusion"),
        "started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"),
        "url": run.get("html_url")
    })


@app.get("/jobs")
def list_jobs(x_api_key: str = Header(...)):
    """Lista os últimos runs do workflow no GitHub."""
    _check_key(x_api_key)

    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN não configurado.")

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/runs",
        headers=headers, params={"per_page": 10}, timeout=15
    )
    runs = resp.json().get("workflow_runs", [])
    return JSONResponse(content={
        "total": len(runs),
        "jobs": [{"id": r["id"], "status": r["status"], "conclusion": r.get("conclusion"),
                  "created_at": r["created_at"], "url": r["html_url"]} for r in runs]
    })
