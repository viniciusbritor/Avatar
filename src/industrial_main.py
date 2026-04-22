import os
import subprocess
import uuid
import time
import requests
from typing import Dict, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from google.cloud import storage

app = FastAPI(title="Brasil AI Industrial Avatar Engine")

# Configurações de Caminhos (Padrão Industrial V17)
VOLUME_PATH = "/workspace"
ASSETS_DIR = "/workspace/latentsync/assets"
TEMP_DIR = "/workspace/outputs/temp"

# Assegurar que diretórios existem
os.makedirs(TEMP_DIR, exist_ok=True)

# --- BIBLIOTECA DE AVATARES ---
TEMPLATES_DIR = f"{VOLUME_PATH}/latentsync/assets"
AVATAR_TEMPLATES = {
    "lana_intro": f"{TEMPLATES_DIR}/lana_base_25fps.mp4",
    "lana_comentario": f"{TEMPLATES_DIR}/lana_base_25fps.mp4",
    "default": f"{TEMPLATES_DIR}/lana_base_25fps.mp4"
}

jobs_db: Dict[str, dict] = {}

@app.get("/health")
def health():
    return {"status": "ok"}

class DIDScript(BaseModel):
    type: str = "audio"
    audio_url: Optional[str] = None
    input: Optional[str] = None

class DIDClipRequest(BaseModel):
    presenter_id: str
    script: DIDScript
    audio_path: Optional[str] = None
    resolution: Optional[int] = 512

@app.get("/health")
def health():
    return {"status": "ok", "gpu": os.path.exists("/dev/nvidia0")}

@app.post("/clips")
async def create_clip(request: DIDClipRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    audio_url = request.script.audio_url
    
    if not audio_url:
        raise HTTPException(status_code=400, detail="Este engine requer audio_url (padrão Brasil-AI).")

    jobs_db[job_id] = {
        "id": job_id,
        "status": "created",
        "created_at": time.time(),
        "result_url": None
    }
    
    background_tasks.add_task(
        run_inference, 
        job_id, 
        audio_url, 
        request.presenter_id
    )
    
    return {"id": job_id, "status": "created"}

@app.get("/clips/{id}")
def get_clip(id: str):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Clip não encontrado")
    return jobs_db[id]

def run_inference(job_id, audio_url, template):
    try:
        jobs_db[job_id]["status"] = "processing"
        
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
            "--video_path", template_video,
            "--audio_path", audio_dest,
            "--video_out_path", video_output,
            "--seed", "1247"
        ]
        
        inf_proc = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd="/workspace/latentsync")
        if inf_proc.returncode != 0:
            raise Exception(f"Inference failed: {inf_proc.stderr}")

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
                
                jobs_db[job_id]["status"] = "completed"
                jobs_db[job_id]["result_url"] = f"gs://brasil-ai-avatars-vault/{remote_path}"
                print(f"🚀 [WORKER] Job {job_id} entregue ao Bucket com sucesso!")
            except Exception as upload_err:
                print(f"❌ [WORKER] Falha no upload GCS: {upload_err}")
                jobs_db[job_id]["status"] = "error"
                jobs_db[job_id]["error"] = f"Upload failed: {str(upload_err)}"
        else:
            print(f"⚠️ [WORKER] Muxing falhou: {mux_proc.stderr}")
            jobs_db[job_id]["status"] = "error"
            jobs_db[job_id]["error"] = f"Muxing failed: {mux_proc.stderr}"

    except Exception as e:
        print(f"❌ [WORKER] Erro no Job {job_id}: {str(e)}")
        jobs_db[job_id]["status"] = "error"
        jobs_db[job_id]["error"] = str(e)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
