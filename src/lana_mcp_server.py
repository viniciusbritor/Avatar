import os
import subprocess
import uuid
import time
import json
import sys
import logging
from fastapi import FastAPI, BackgroundTasks
import uvicorn

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

app = FastAPI(title="Lana MCP Server - Industrial HTTP Mode v2.6")
JOBS_FILE = "/workspace/lana_jobs.json"

def load_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_jobs():
    try:
        with open(JOBS_FILE, 'w') as f:
            json.dump(JOBS, f)
    except: pass

JOBS = load_jobs()

@app.post("/clips")
async def create_render_job(payload: dict, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    audio_url = payload.get("audio_url")
    presenter_id = payload.get("presenter_id", "lana_comentario")
    
    logging.info(f"[MCP] Recebido Job {job_id} | Audio: {audio_url}")
    
    JOBS[job_id] = {"status": "starting", "progress": 0, "audio_url": audio_url, "presenter_id": presenter_id}
    save_jobs()
    
    # Inicia o processamento em background
    background_tasks.add_task(run_inference, job_id, audio_url, presenter_id)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/clips/{job_id}")
async def get_status(job_id: str):
    return JOBS.get(job_id, {"error": "Job not found"})

def run_inference(job_id, audio_url, presenter_id):
    try:
        JOBS[job_id]["status"] = "processing"
        save_jobs()
        
        # O script industrial_main.py está em /workspace/src/ na imagem v2.2 base
        cmd = [
            "python3", "/workspace/src/industrial_main.py",
            "--audio", audio_url,
            "--presenter", presenter_id,
            "--job-id", job_id
        ]
        
        logging.info(f"[MCP] Executando: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd="/workspace")
        
        for line in process.stdout:
            logging.info(f"[RENDER-LOG] {line.strip()}")
            if "Progress:" in line:
                try:
                    prog = int(line.split("Progress:")[1].split("%")[0])
                    JOBS[job_id]["progress"] = prog
                    save_jobs()
                except: pass
        
        process.wait()
        if process.returncode == 0:
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["progress"] = 100
        else:
            JOBS[job_id]["status"] = "failed"
        save_jobs()
            
    except Exception as e:
        logging.error(f"[MCP] Falha no Job {job_id}: {e}")
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        save_jobs()

if __name__ == "__main__":
    logging.info("Iniciando Lana MCP Server v2.7 SOBERANO na porta 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
