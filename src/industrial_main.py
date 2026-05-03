import os
import subprocess
import uuid
import time
import json
import threading
import requests
from typing import Dict, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from google.cloud import storage, firestore

app = FastAPI(title="Brasil AI Industrial Avatar Engine")

# Configurações de Caminhos (Padrão Industrial V17)
VOLUME_PATH = "/workspace"
ASSETS_DIR = "/workspace/latentsync/assets"
TEMP_DIR = "/workspace/outputs/temp"

# Assegurar que diretórios existem
os.makedirs(TEMP_DIR, exist_ok=True)

# --- BIBLIOTECA DE AVATARES (Sincronizada via Bucket) ---
TEMPLATES_DIR = f"{VOLUME_PATH}/latentsync/assets"
AVATAR_TEMPLATES = {
    "lana_intro": f"{TEMPLATES_DIR}/lana_intro.mp4",
    "lana_comentario": f"{TEMPLATES_DIR}/lana_comentario.mp4",
    "lana_benchmark": f"{TEMPLATES_DIR}/lana_benchmark.mp4",
    "default": f"{TEMPLATES_DIR}/lana_base_25fps.mp4"
}

import json

JOBS_FILE = f"{VOLUME_PATH}/jobs_db.json"

def load_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_jobs(jobs):
    try:
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs, f)
    except:
        pass

jobs_db: Dict[str, dict] = load_jobs()

def update_job_status(job_id, status, result_url=None, error=None):
    if job_id not in jobs_db:
        jobs_db[job_id] = {"id": job_id, "created_at": time.time()}
    jobs_db[job_id]["status"] = status
    if result_url: jobs_db[job_id]["result_url"] = result_url
    if error: jobs_db[job_id]["error"] = error
    save_jobs(jobs_db)

class DIDScript(BaseModel):
    type: str = "audio"
    audio_url: Optional[str] = None
    input: Optional[str] = None

class DIDClipRequest(BaseModel):
    presenter_id: str
    script: DIDScript
    audio_path: Optional[str] = None
    resolution: Optional[int] = 512
    webhook_url: Optional[str] = None
    job_id: Optional[str] = None

# LOCK DE ESCALA HORIZONTAL
IS_BUSY = False

@app.get("/health")
def health():
    return {"status": "ok", "gpu": os.path.exists("/dev/nvidia0"), "busy": IS_BUSY}

@app.post("/clips")
async def create_clip(request: DIDClipRequest, background_tasks: BackgroundTasks):
    global IS_BUSY
    if IS_BUSY:
        raise HTTPException(status_code=429, detail="GPU is currently busy. Scale-out required.")
        
    # Aceita job_id externo ou gera um novo
    job_id = request.job_id or str(uuid.uuid4())
    audio_url = request.script.audio_url
    
    if not audio_url:
        raise HTTPException(status_code=400, detail="Este engine requer audio_url (padrão Brasil-AI).")

    IS_BUSY = True
    update_job_status(job_id, "created")
    
    background_tasks.add_task(
        run_inference_wrapper, 
        job_id, 
        audio_url, 
        request.presenter_id,
        request.webhook_url
    )
    
    return {"id": job_id, "status": "created"}

@app.get("/clips/{id}")
def get_clip(id: str):
    global jobs_db
    jobs_db = load_jobs() # Recarregar para ver mudanças de background tasks
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Clip não encontrado")
    return jobs_db[id]

def notify_webhook(webhook_url: str, payload: dict):
    if not webhook_url: return
    print(f"🔗 [WEBHOOK] Enviando callback para {webhook_url}")
    api_key = os.environ.get("API_SECRET_KEY", "brasilai-avatar-2026")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    import time
    for attempt in range(5):
        try:
            res = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                print("✅ [WEBHOOK] Callback entregue com sucesso.")
                return
            print(f"⚠️ [WEBHOOK] Tentativa {attempt+1} retornou status {res.status_code}")
        except Exception as e:
            print(f"❌ [WEBHOOK] Erro ao chamar webhook (Tentativa {attempt+1}): {e}")
        time.sleep(5)
    print("❌ [WEBHOOK] Desistindo de enviar callback após 5 tentativas.")

def run_inference_wrapper(*args, **kwargs):
    global IS_BUSY
    try:
        run_inference(*args, **kwargs)
    finally:
        print("🔓 [WORKER] Lock liberado. GPU pronta para novo Job.")
        IS_BUSY = False

def run_inference(job_id, audio_url, template, webhook_url=None):
    try:
        update_job_status(job_id, "processing")
        
        # 1. Preparar caminhos
        audio_dest = f"{TEMP_DIR}/{job_id}_audio.wav"
        video_output = f"{TEMP_DIR}/{job_id}_video.mp4"
        final_output = f"{TEMP_DIR}/{job_id}_final.mp4"
        
        # 2. Download Áudio
        download_file(audio_url, audio_dest)
        
        # 3. Escolher Template
        template_video = AVATAR_TEMPLATES.get(template, AVATAR_TEMPLATES["default"])
        
        # 4. LatentSync Inference
        print(f"🚀 [WORKER] Iniciando Job {job_id}...")
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        
        cmd = [
            "python3", "scripts/inference.py",
            "--unet_config_path", "configs/unet/stage2_512.yaml",
            "--inference_ckpt_path", "/workspace/latentsync/checkpoints/latentsync_unet.pt",
            "--guidance_scale", "1.5",
            "--inference_steps", "20",
            "--enable_deepcache",
            "--video_path", template_video,
            "--audio_path", audio_dest,
            "--video_out_path", video_output,
        ]
        
        log_file = f"{TEMP_DIR}/{job_id}_render.log"
        with open(log_file, "w") as f_log:
            inf_proc = subprocess.run(cmd, env=env, stdout=f_log, stderr=f_log, text=True, cwd="/workspace/latentsync")
            
        if inf_proc.returncode != 0:
            with open(log_file, "r") as f_log:
                err_content = f_log.read()
            raise Exception(f"Inference failed: {err_content}")

        # 5. Mux Audio/Video (Sync corrigido)
        # Usamos -shortest e streams específicos para garantir sincronia
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", video_output,
            "-i", audio_dest,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            final_output
        ]
        
        mux_proc = subprocess.run(mux_cmd, capture_output=True, text=True)
        
        if mux_proc.returncode == 0:
            print(f"✅ [WORKER] Muxing concluído para {job_id}")
            
            # 6. Upload para GCS (Padrão Industrial V19)
            remote_filename = f"final_{job_id}.mp4"
            remote_path = f"outputs/{remote_filename}"
            print(f"📦 [GCS] Iniciando upload: {remote_path}")
            
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket("brasil-ai-avatars-vault")
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(final_output)
                
                final_gcs_url = f"gs://brasil-ai-avatars-vault/{remote_path}"
                update_job_status(job_id, "completed", result_url=final_gcs_url)
                print(f"🚀 [WORKER] Job {job_id} entregue ao Bucket com sucesso!")
                
                # Notifica Cloud Run!
                notify_webhook(webhook_url, {
                    "job_id": job_id,
                    "status": "completed",
                    "video_path": final_gcs_url
                })
                
                # Zero-Waste: Se o processo foi um sucesso absoluto e comunicou a API, 
                # podemos já dar um hint para o Sentinela desligar a máquina
                os.system("touch /workspace/idle_now")
                
            except Exception as upload_err:
                print(f"❌ [WORKER] Falha no upload GCS: {upload_err}")
                update_job_status(job_id, "error", error=f"Upload failed: {str(upload_err)}")
                notify_webhook(webhook_url, {"job_id": job_id, "status": "failed", "error": f"Upload fail: {str(upload_err)}"})
        else:
            print(f"⚠️ [WORKER] Muxing falhou: {mux_proc.stderr}")
            update_job_status(job_id, "error", error=f"Muxing failed: {mux_proc.stderr}")
            notify_webhook(webhook_url, {"job_id": job_id, "status": "failed", "error": f"Muxing failed: {mux_proc.stderr}"})

    except Exception as e:
        print(f"❌ [WORKER] Erro no Job {job_id}: {str(e)}")
        update_job_status(job_id, "error", error=str(e))
        notify_webhook(webhook_url, {"job_id": job_id, "status": "failed", "error": str(e)})

def download_file(url: str, dest: str):
    if url.startswith("gs://"):
        print(f"📦 [WORKER] Baixando via GCS Nativo: {url}")
        # Parse gs://bucket/path
        parts = url.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1]
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(dest)
    else:
        print(f"🌐 [WORKER] Baixando via HTTP: {url}")
        r = requests.get(url)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)

def poll_pending_jobs():
    """Polling continuo com auto-shutdown: idle 15min, after-job 5min, dead man 120min."""
    global IS_BUSY
    print("[POLLER] Iniciando watcher de jobs (shutdown: idle=15min, after-job=5min)...")
    idle_count = 0
    MAX_IDLE = 90  # 90 × 10s = 15 min
    cooldown = False
    cooldown_count = 0
    COOLDOWN_MAX = 30  # 30 × 10s = 5 min

    while True:
        try:
            if IS_BUSY:
                time.sleep(10)
                continue

            if cooldown:
                cooldown_count += 1
                if cooldown_count >= COOLDOWN_MAX:
                    remaining = list(db.collection("avatar_jobs")
                                     .where("status", "==", "queued").limit(1).stream())
                    if not remaining:
                        print(f"[POLLER] {COOLDOWN_MAX*10//60}min sem novos jobs. Desligando GPU...")
                        os.system("sudo shutdown -h now")
                        break
                    else:
                        print("[POLLER] Novos jobs detectados. Cancelando cooldown.")
                        cooldown = False
                        cooldown_count = 0
                time.sleep(10)
                continue

            db = firestore.Client(project="brasili-ia-news")
            docs = list(db.collection("avatar_jobs")
                        .where("status", "==", "queued")
                        .limit(10).stream())
            found = False
            for doc in docs:
                job = doc.to_dict()
                job_id = job.get("job_id", doc.id)
                audio_url = job.get("audio_url", "")
                if not audio_url:
                    continue
                if IS_BUSY:
                    break
                db.collection("avatar_jobs").document(job_id).update({"status": "running"})
                IS_BUSY = True
                idle_count = 0
                cooldown = True
                cooldown_count = 0
                found = True
                print(f"[POLLER] Job {job_id} iniciado. Cooldown de {COOLDOWN_MAX*10//60}min apos termino.")
                presenter = job.get("presenter_id", "default")
                webhook_url = job.get("webhook_url", "")
                threading.Thread(
                    target=run_inference_wrapper,
                    args=(job_id, audio_url, presenter, webhook_url),
                    daemon=True
                ).start()
                break

            if not found:
                idle_count += 1
                if idle_count >= MAX_IDLE:
                    print(f"[POLLER] {MAX_IDLE*10//60} min ocioso. Desligando GPU...")
                    os.system("sudo shutdown -h now")
                    break

        except Exception as e:
            print(f"[POLLER] Erro: {e}")
        time.sleep(10)

@app.on_event("startup")
def on_startup():
    threading.Thread(target=poll_pending_jobs, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
