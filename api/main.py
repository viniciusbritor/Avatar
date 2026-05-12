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
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.cloud import compute_v1
from google.cloud.compute_v1.types import (
    Instance, AttachedDisk, AttachedDiskInitializeParams,
    AcceleratorConfig, NetworkInterface, AccessConfig,
    ServiceAccount, Metadata, Items, Scheduling,
    ListInstancesRequest
)
from google.api_core import exceptions as gcp_exceptions

from src.agente_lana_orchestrator import AgenteLanaOrchestrator, L4_MACHINE, PROVISIONING_MODEL
from .secrets_manager import get_secret

BRT = timezone(timedelta(hours=-3))

ZONES = ["us-east1-c", "us-west4-a", "us-east1-d", "us-east4-a", "us-west1-a",
         "us-central1-a", "us-east5-a", "us-south1-a", "europe-west4-a",
         "europe-west1-b", "europe-west6-b", "asia-east1-a",
         "northamerica-northeast1-b"]

PROJECT = "brasili-ia-news"

try:
    from google.cloud import firestore
    db = firestore.Client(project="brasili-ia-news")
    JOBS_COLLECTION = db.collection('avatar_jobs')
    GPU_STATUS = db.collection('gpu_status')
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


def _cleanup_l4_residue(project: str):
    """Remove todas as instâncias L4 terminadas e seus discos (Zero-Waste)."""
    try:
        client = compute_v1.InstancesClient()
        for zone in ZONES:
            try:
                request = ListInstancesRequest(
                    project=project, zone=zone,
                    filter='name:"lana-engine-" AND status = "TERMINATED"'
                )
                for instance in client.list(request=request):
                    name = instance.name
                    print(f"[ZERO-WASTE] Purgando resíduo L4: {name} em {zone}")
                    client.delete(project=project, zone=zone, instance=name)
            except gcp_exceptions.NotFound:
                pass
            except gcp_exceptions.GoogleAPICallError as e:
                print(f"[ZERO-WASTE] Erro em {zone}: {e}")
    except Exception as e:
        print(f"[ZERO-WASTE] Erro na limpeza de resíduos: {e}")


def _update_gpu_status(state: str, instance_name: str = "", zone: str = "", message: str = ""):
    """Escreve estado da GPU no Firestore para dashboard near-real-time."""
    if not db:
        return
    try:
        GPU_STATUS.document("latest").set({
            "state": state,
            "instance": instance_name,
            "zone": zone,
            "message": message,
            "updated_at": datetime.now(BRT).isoformat()
        })
    except Exception as e:
        print(f"[DASHBOARD] Erro ao atualizar GPU status: {e}")


def _scan_garbage():
    """Varre instancias L4 TERMINATED e discos orfaos (custo desnecessario)."""
    garbage = {"instances": [], "disks": [], "total_monthly_cost_usd": 0.0}
    try:
        client = compute_v1.InstancesClient()
        for zone in ZONES:
            try:
                request = ListInstancesRequest(
                    project=PROJECT, zone=zone,
                    filter='name:"lana-engine-" AND status = "TERMINATED"'
                )
                for instance in client.list(request=request):
                    garbage["instances"].append({
                        "name": instance.name, "zone": zone, "status": "TERMINATED",
                        "disk_cost": "~$4/mes"
                    })
            except gcp_exceptions.NotFound:
                pass
            except gcp_exceptions.GoogleAPICallError as e:
                print(f"[SCAN] Erro em {zone}: {e}")
        garbage["total_monthly_cost_usd"] = len(garbage["instances"]) * 4.0
    except Exception as e:
        garbage["error"] = str(e)
    return garbage


def _spawn_gpu():
    """Background: liga ou cria VM L4 com retry 3x. Sem SSH."""
    IMAGE_FAMILY = "common-cu129-ubuntu-2204-nvidia-580"
    IMAGE_PROJECT = "deeplearning-platform-release"

    import uuid as _uuid
    import time as _time

    _cleanup_l4_residue(PROJECT)
    _update_gpu_status("cleanup", message="Limpando residuos de L4 anteriores")

    # Carrega startup-script do disco do container
    try:
        with open("/app/infra/boot/startup_arch4.sh", "r") as f:
            STARTUP_SCRIPT = f.read()
    except Exception:
        STARTUP_SCRIPT = "#!/bin/bash\necho 'startup_arch4.sh nao encontrado'"

    client = compute_v1.InstancesClient()

    for attempt in range(3):
        try:
            # Reusa GPU existente RUNNING
            found = False
            for zone in ZONES:
                try:
                    request = ListInstancesRequest(
                        project=PROJECT, zone=zone,
                        filter='name:"lana-engine-" AND status = "RUNNING"'
                    )
                    instances = list(client.list(request=request))
                    if instances:
                        inst = sorted(instances, key=lambda x: x.name, reverse=True)[0]
                        name, zone_str = inst.name, zone
                        print(f"[SPAWN] GPU ja ativa: {name} em {zone_str}")
                        _update_gpu_status("ready", instance_name=name, zone=zone_str,
                                           message="GPU L4 ativa e pronta")
                        found = True
                        break
                except gcp_exceptions.NotFound:
                    continue
                except gcp_exceptions.GoogleAPICallError:
                    continue
            if found:
                return

            for zone in ZONES:
                name = f"lana-engine-l4-{int(_time.time())}-{_uuid.uuid4().hex[:4]}"
                print(f"[SPAWN] Tentativa {attempt+1}/3 — Criando {name} em {zone}...")
                _update_gpu_status("spawning", instance_name=name, zone=zone,
                                   message=f"Criando VM L4 em {zone} (tentativa {attempt+1}/3)")
                try:
                    instance = Instance(
                        name=name,
                        machine_type=f"zones/{zone}/machineTypes/{L4_MACHINE}",
                        disks=[AttachedDisk(
                            boot=True,
                            auto_delete=True,
                            initialize_params=AttachedDiskInitializeParams(
                                disk_size_gb=100,
                                source_image=f"projects/{IMAGE_PROJECT}/global/images/family/{IMAGE_FAMILY}"
                            )
                        )],
                        network_interfaces=[NetworkInterface(
                            name="nic0",
                            access_configs=[AccessConfig(
                                name="External NAT",
                                type_="ONE_TO_ONE_NAT"
                            )]
                        )],
                        service_accounts=[ServiceAccount(
                            email="default",
                            scopes=["https://www.googleapis.com/auth/cloud-platform"]
                        )],
                        scheduling=Scheduling(
                            provisioning_model=PROVISIONING_MODEL,
                            on_host_maintenance="TERMINATE"
                        ),
                        guest_accelerators=[AcceleratorConfig(
                            accelerator_count=1,
                            accelerator_type=f"projects/{PROJECT}/zones/{zone}/acceleratorTypes/nvidia-l4"
                        )],
                        metadata=Metadata(
                            items=[Items(key="startup-script", value=STARTUP_SCRIPT)]
                        )
                    )
                    client.insert(project=PROJECT, zone=zone, instance_resource=instance)
                    print(f"[SPAWN] GPU criada: {name} em {zone}")
                    _update_gpu_status("booting", instance_name=name, zone=zone,
                                       message="VM criada. Boot iniciando (Docker + Sentinel)")
                    return
                except gcp_exceptions.ResourceExhausted:
                    print(f"[SPAWN] Cota cheia ou stockout em {zone}, tentando proxima zona...")
                    continue
                except gcp_exceptions.GoogleAPICallError as e:
                    err = str(e)[:200]
                    print(f"[SPAWN] Erro em {zone}: {err}")
                    continue
        except Exception as e:
            print(f"[SPAWN] Erro tentativa {attempt+1}: {e}")
        if attempt < 2:
            _time.sleep(30)
    print("[SPAWN] GPU L4 nao encontrada apos 3 tentativas.")
    _update_gpu_status("failed", message="Falha: GPU L4 nao encontrada apos 3 tentativas")


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
        _update_gpu_status("idle", message="Render concluido. GPU aguardando proximo job.")
    else:
        doc_ref.update({
            "status": "failed",
            "message": f"Falha na GPU: {payload.error}",
            "completed_at": datetime.now(BRT).isoformat()
        })
        _update_gpu_status("error", message=f"Render falhou: {payload.error}")
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


@app.get("/dashboard")
def dashboard():
    """Painel near-real-time: GPU status + ultimos jobs. Para Google Stitch."""
    data = {
        "timestamp": datetime.now(BRT).isoformat(),
        "gpu": {"state": "unknown", "instance": "", "zone": "", "message": ""},
        "last_jobs": [],
        "summary": {"total_completed": 0, "total_failed": 0, "in_progress": 0}
    }
    
    if not db:
        data["error"] = "Firestore indisponivel"
    return JSONResponse(content=data)


@app.get("/panel", response_class=HTMLResponse, include_in_schema=False)
def panel():
    """Painel Lana Industrial — GPU, Jobs, Lixo Zero-Waste."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>Lana Industrial — Painel Zero-Waste</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0f; color: #e0e0e0; font-family: 'Courier New', monospace; padding: 20px; }
h1 { color: #00ff88; font-size: 18px; margin-bottom: 16px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #141418; border: 1px solid #2a2a35; border-radius: 6px; padding: 14px; }
.card h2 { font-size: 13px; color: #888; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px; }
.state { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; }
.cleanup { background: #333; color: #aaa; }
.spawning { background: #0066ff; color: #fff; }
.booting { background: #ff8800; color: #fff; }
.ready { background: #00cc44; color: #000; }
.rendering { background: #cc00ff; color: #fff; }
.idle { background: #555; color: #aaa; }
.error { background: #ff0044; color: #fff; }
.failed { background: #ff0044; color: #fff; }
.info { font-size: 11px; color: #666; margin-top: 4px; }
.garbage { border-color: #ff4444; background: #1a1014; }
.garbage h2 { color: #ff4444; }
.garbage-item { font-size: 11px; color: #ff6666; padding: 2px 0; }
.cost { color: #ffaa00; font-weight: bold; }
.job { font-size: 11px; padding: 4px 0; border-bottom: 1px solid #1a1a22; }
.job-id { color: #00aaff; }
.job-status { font-weight: bold; }
.completed { color: #00cc44; }
.queued { color: #ffaa00; }
.failed { color: #ff4444; }
.processing { color: #cc00ff; }
.summary { display: flex; gap: 16px; margin-top: 8px; }
.summary-item { font-size: 12px; }
.summary-item span { font-size: 20px; font-weight: bold; }
.progress-wrap { margin-top: 8px; background: #1a1a25; border-radius: 4px; height: 20px; overflow: hidden; }
.progress-bar { height: 100%; border-radius: 4px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #000; }
.progress-loading { background: linear-gradient(90deg, #0066ff, #00aaff); }
.progress-face_detect { background: linear-gradient(90deg, #00cc88, #00ffaa); }
.progress-inference { background: linear-gradient(90deg, #8800ff, #cc00ff); }
.progress-restore { background: linear-gradient(90deg, #ff8800, #ffaa00); }
.progress-encoding { background: linear-gradient(90deg, #ffcc00, #ffdd44); }
.progress-done { background: linear-gradient(90deg, #00cc44, #00ff66); }
.footer { margin-top: 16px; font-size: 10px; color: #444; text-align: center; }
.refresh { animation: pulse 2s infinite; }
@keyframes pulse { 0%{opacity:1} 50%{opacity:0.5} 100%{opacity:1} }
</style>
</head>
<body>
<h1>⚡ Lana Industrial — Painel Zero-Waste</h1>
<div class="grid">
  <div class="card">
    <h2>GPU L4</h2>
    <div id="gpu-state">Carregando...</div>
    <div id="gpu-info" class="info"></div>
    <div id="progress-container" style="display:none">
      <div class="progress-wrap"><div id="progress-bar" class="progress-bar" style="width:0%"></div></div>
    </div>
  </div>
  <div class="card garbage">
    <h2>🗑️ Lixo Detectado (custo desnecessário)</h2>
    <div id="garbage">Carregando...</div>
  </div>
  <div class="card">
    <h2>Resumo (últimos 20 jobs)</h2>
    <div id="summary"></div>
  </div>
  <div class="card">
    <h2>Últimos Jobs</h2>
    <div id="jobs"></div>
  </div>
</div>
<div class="footer"><span class="refresh" id="clock"></span> — polling a cada 5s</div>
<script>
async function refresh() {
  try {
    const r = await fetch('/dashboard');
    const d = await r.json();
    document.getElementById('clock').textContent = d.timestamp || '';
    
    // GPU
    const g = d.gpu;
    const gpuEl = document.getElementById('gpu-state');
    gpuEl.innerHTML = '<span class="state ' + (g.state||'unknown') + '">' + (g.state||'?').toUpperCase() + '</span>';
    document.getElementById('gpu-info').textContent = (g.instance ? g.instance + ' @ ' + g.zone : '') + ' — ' + (g.message || '');
    
    // Progress bar (parse phase/percent from message like "[inference] chunk 3/16 (35%)")
    const msg = g.message || '';
    const pctMatch = msg.match(/\((\d+)%\)/);
    const phaseMatch = msg.match(/\[(\w+)\]/);
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    if (pctMatch && phaseMatch && g.state === 'rendering') {
      const pct = parseInt(pctMatch[1]);
      const phase = phaseMatch[1];
      progressContainer.style.display = 'block';
      progressBar.style.width = pct + '%';
      progressBar.textContent = pct + '%';
      progressBar.className = 'progress-bar progress-' + phase;
    } else if (g.state === 'idle' || g.state === 'ready') {
      progressContainer.style.display = 'none';
    }
    
    // Garbage
    const gb = d.garbage || {};
    let gbHtml = '';
    if (gb.instances && gb.instances.length > 0) {
      gbHtml += '<div class="cost">Custo mensal estimado: ~$' + gb.total_monthly_cost_usd + '/mês</div>';
      gb.instances.forEach(i => {
        gbHtml += '<div class="garbage-item">⚠️ ' + i.name + ' @ ' + i.zone + ' (' + i.status + ') — ' + i.disk_cost + '</div>';
      });
    } else {
      gbHtml = '<div style="color:#00cc44;font-size:12px;">✅ Nenhum lixo detectado</div>';
    }
    document.getElementById('garbage').innerHTML = gbHtml;
    
    // Summary
    const s = d.summary;
    document.getElementById('summary').innerHTML = `
      <div class="summary-item">✅ Concluídos: <span style="color:#00cc44">${s.total_completed}</span></div>
      <div class="summary-item">❌ Falhas: <span style="color:#ff4444">${s.total_failed}</span></div>
      <div class="summary-item">⏳ Em andamento: <span style="color:#ffaa00">${s.in_progress}</span></div>
    `;
    
    // Jobs
    let jHtml = '';
    (d.last_jobs || []).forEach(j => {
      jHtml += '<div class="job"><span class="job-id">#' + (j.job_id||'?').substring(0,8) + '</span> ';
      jHtml += '<span class="job-status ' + (j.status||'') + '">' + (j.status||'?') + '</span> ';
      jHtml += '<span style="color:#666;font-size:10px">' + (j.text||'').substring(0,40) + '</span>';
      if (j.video_path) jHtml += ' 📹';
      jHtml += '</div>';
    });
    document.getElementById('jobs').innerHTML = jHtml || 'Nenhum job';
  } catch(e) {
    console.error(e);
  }
}
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>""")
    
    try:
        # GPU status
        gpu_doc = GPU_STATUS.document("latest").get()
        if gpu_doc.exists:
            data["gpu"] = gpu_doc.to_dict()
        
        # Lixo (instancias TERMINATED)
        data["garbage"] = _scan_garbage()
        
        # Ultimos 5 jobs
        job_docs = JOBS_COLLECTION.order_by("created_at", direction=firestore.Query.DESCENDING).limit(5).stream()
        for doc in job_docs:
            data["last_jobs"].append(doc.to_dict())
        
        # Resumo dos ultimos 20 jobs
        all_docs = JOBS_COLLECTION.order_by("created_at", direction=firestore.Query.DESCENDING).limit(20).stream()
        for doc in all_docs:
            job = doc.to_dict()
            if job.get("status") == "completed":
                data["summary"]["total_completed"] += 1
            elif job.get("status") == "failed" or job.get("status") == "error":
                data["summary"]["total_failed"] += 1
            elif job.get("status") in ("queued", "processing"):
                data["summary"]["in_progress"] += 1
    except Exception as e:
        data["error"] = str(e)
    
    return JSONResponse(content=data)
