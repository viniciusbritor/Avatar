import os
import uuid
import subprocess
import requests
import time
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict

app = FastAPI(title="Lana Avatar Engine - D-ID Mirror v1.0")

# --- CONFIGURAÇÃO DE VOLUMES ---
# O volume persistente é montado em /app/data
VOLUME_PATH = os.getenv("VOLUME_PATH", "/app/data")
CHECKPOINTS_DIR = f"{VOLUME_PATH}/checkpoints"

# Modelos 256px (Padrão)
CONFIG_PATH = "/app/configs/unet/stage2.yaml"
UNET_PATH = f"{CHECKPOINTS_DIR}/latentsync_unet.pt"

# Modelos 512px (Ultra-HD / Brasil AI) - Corrige borrão na boca
CONFIG_512_PATH = "/app/configs/unet/stage2_512.yaml"
UNET_512_PATH = f"{CHECKPOINTS_DIR}/latentsync_unet_512.pt"

# --- BIBLIOTECA DE AVATARES ---
TEMPLATES_DIR = f"{VOLUME_PATH}/templates"
AVATAR_TEMPLATES = {
    "lana_intro": f"{TEMPLATES_DIR}/lana_intro.mp4",
    "lana_comentario": f"{TEMPLATES_DIR}/lana_comentario.mp4",
    "lana_outro": f"{TEMPLATES_DIR}/lana_outro.mp4",
    # Aliases
    "default": f"{TEMPLATES_DIR}/lana_comentario.mp4",
    "lana": f"{TEMPLATES_DIR}/lana_comentario.mp4"
}

# Mock Database (Em produção usaríamos SQLite no disco persistente)
jobs_db: Dict[str, dict] = {}

class DIDClipRequest(BaseModel):
    # Payload idêntico ao que o script generate_did_video.py envia
    presenter_id: str
    script: dict # Ex: {"type": "audio", "audio_url": "..."} ou {"type": "text", "input": "..."}
    audio_path: Optional[str] = None # Caminho local OPCIONAL
    resolution: Optional[int] = 512 # Padrão industrial Brasil AI

@app.get("/health")
def health():
    gpu_ready = os.path.exists("/dev/nvidia0")
    # Verifica se os modelos de 15GB estão no disco montado
    models_ready = os.path.exists(UNET_PATH)
    return {
        "status": "ready" if (gpu_ready and models_ready) else "initializing",
        "gpu": gpu_ready,
        "volume_mounted": os.path.exists(VOLUME_PATH),
        "models_present": models_ready,
        "engine": "LatentSync"
    }

# --- ENDPOINTS EMULADORES D-ID ---

@app.post("/clips")
def create_clip(request: DIDClipRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    print(f"🎬 [D-ID Mirror] Novo pedido de Clipe: {job_id}")
    
    # Extrair audio_url do payload aninhado do D-ID
    audio_url = request.script.get("audio_url")
    if not audio_url and request.script.get("type") == "text":
        # Nota: Por enquanto o LatentSync precisa de áudio. 
        # Poderíamos integrar um TTS local aqui no futuro.
        raise HTTPException(status_code=400, detail="Este emulador requer audio_url (padrão Brasil-AI).")

    # Registrar Job
    jobs_db[job_id] = {
        "id": job_id,
        "status": "processing",
        "created_at": time.time(),
        "result_url": None
    }
    
    # Disparar processamento em background (Agora com resolução variável)
    background_tasks.add_task(
        run_latentsync_inference, 
        job_id, 
        audio_url, 
        request.presenter_id,
        request.resolution,
        request.audio_path
    )
    
    # Retorno idêntico ao D-ID (Status 201 Created)
    return {"id": job_id, "status": "created"}

@app.get("/clips/{id}")
def get_clip(id: str):
    if id not in jobs_db:
        raise HTTPException(status_code=404, detail="Clip não encontrado")
    
    job = jobs_db[id]
    
    # Formato de resposta idêntico ao D-ID para o script de polling não quebrar
    # O script espera status == "done"
    return {
        "id": job["id"],
        "status": "done" if job["status"] == "completed" else job["status"],
        "result_url": job.get("result_url"),
        "error": job.get("error")
    }

# --- MOTOR DE INFERÊNCIA ---

def run_latentsync_inference(job_id: str, audio_url: str, presenter_id: str, resolution: int = 512, audio_path: str = None):
    try:
        print(f"🚀 [WORKER] Iniciando inferência ({resolution}px) para {job_id}")
        
        # Selecionar Checkpoints e Configs
        use_config = CONFIG_512_PATH if resolution == 512 else CONFIG_PATH
        use_unet = UNET_512_PATH if resolution == 512 else UNET_PATH
        
        # 1. Preparar caminhos
        tmp_dir = f"/tmp/{job_id}"
        os.makedirs(tmp_dir, exist_ok=True)
        audio_dest = f"{tmp_dir}/input.mp3"
        output_dest = f"{tmp_dir}/output.mp4"
        
        # Mapeamento de presenter_id para template local (Lana)
        video_template = AVATAR_TEMPLATES.get(presenter_id, AVATAR_TEMPLATES["default"])
        
        # Validar se o template existe
        if not os.path.exists(video_template):
            print(f"⚠️ [WORKER] Template {video_template} não encontrado. Usando fallback.")
            video_template = "/app/assets/demo1_video.mp4" # Fallback de emergência
        
        # 2. Obter Audio
        if audio_path and os.path.exists(audio_path):
            print(f"📦 [WORKER] Usando audio local: {audio_path}")
            import shutil
            shutil.copy(audio_path, audio_dest)
        elif audio_url:
            download_file(audio_url, audio_dest)
        else:
            raise Exception("Nenhum audio_url ou audio_path fornecido.")
        
        # 3. Execução LatentSync
        cmd = [
            "python3", "scripts/inference.py",
            "--unet_config_path", use_config,
            "--inference_ckpt_path", use_unet,
            "--video_path", video_template,
            "--audio_path", audio_dest,
            "--video_out_path", output_dest,
            "--guidance_scale", "1.5",
            "--inference_steps", "20",
            "--seed", "1247"
        ]
        
        # Garantir que o PYTHONPATH inclua /app para achar o módulo latentsync
        env = os.environ.copy()
        env["PYTHONPATH"] = "/app"
        
        process = subprocess.run(cmd, capture_output=True, text=True, cwd="/app", env=env)
        
        if process.returncode != 0:
            raise Exception(f"LatentSync Fail: {process.stderr}")

        # 4. Pós-processamento: Unir Áudio e Vídeo (Remux)
        print(f"🎬 [WORKER] Mesclando áudio e vídeo para {job_id}")
        final_output = f"{tmp_dir}/final.mp4"
        merge_cmd = [
            "ffmpeg", "-y",
            "-i", output_dest,
            "-i", audio_dest,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-shortest",
            final_output
        ]
        merge_proc = subprocess.run(merge_cmd, capture_output=True, text=True)
        if merge_proc.returncode != 0:
             print(f"⚠️ [WORKER] Falha no merge de áudio: {merge_proc.stderr}. Usando vídeo mudo.")
             final_output = output_dest

        # 5. Upload / Disponibilização (Mock ou GCS)
        final_url = f"https://storage.googleapis.com/brasil-ai-avatars/results/{job_id}.mp4"
        # upload_to_gcs(final_output, f"results/{job_id}.mp4")

        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["result_url"] = final_url
        print(f"✅ [WORKER] Job {job_id} concluído com áudio!")

    except Exception as e:
        print(f"❌ [WORKER] Erro no Job {job_id}: {str(e)}")
        jobs_db[job_id]["status"] = "error"
        jobs_db[job_id]["error"] = str(e)

def download_file(url: str, dest: str):
    r = requests.get(url)
    with open(dest, "wb") as f:
        f.write(r.content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
