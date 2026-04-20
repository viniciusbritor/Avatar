import os
import time
import requests
import subprocess
import json
import sqlite3
from agno.agent import Agent
from google.cloud import storage

# --- CONFIGURAÇÕES SOBERANAS (PROJETO AVATAR) ---
PROJECT_ID = "brasili-ia-news"
BUCKET_NAME = "brasil-ia-lana-assets"
INSTANCE_NAME = "lana-industrial-prod"
ZONE = "us-east1-c"
GOLD_IMAGE = "projects/brasili-ia-news/global/images/lana-gold-standard-v18"
ELEVENLABS_API_KEY = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Sarah (Official Project Standard)

class LanaIndustrialEngine:
    """Ferramentas de infraestrutura GCP com Inteligência Maestro V18 (Gold Standard)."""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.preferred_instance = {"name": INSTANCE_NAME, "zone": ZONE, "type": "L4"}
        self.failover_zones = ["us-east1-c", "us-east1-b", "us-central1-a"]
        self.active_instance = None
        self.active_zone = None

    def discover_active_instance(self):
        """Procura por instâncias Lana já ligadas para reuso imediato (FinOps)."""
        print("[MAESTRO] Escaneando máquinas ativas no radar...")
        cmd = ["gcloud", "compute", "instances", "list", 
               "--project", self.project_id, "--filter=status=RUNNING", 
               "--format=json", "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        try:
            instances = json.loads(res.stdout)
            for inst in instances:
                if "lana-engine" in inst["name"]:
                    print(f"[MAESTRO] Máquina ENCONTRADA: {inst['name']} ativa em {inst['zone'].split('/')[-1]}.")
                    self.active_instance = inst["name"]
                    self.active_zone = inst["zone"].split("/")[-1]
                    return True
        except: pass
        return False

    def ensure_instance_ready(self):
        """Garante uma máquina pronta via Reuso, Start ou Spawn de Imagem Gold."""
        # 1. Tentar Reuso
        if self.discover_active_instance():
            self.bootstrap_v18(is_prebaked=True)
            return self.get_ip()

        # 2. Tentar Ligar a Principal (us-east4)
        print(f"[MAESTRO] Tentando despertar {self.preferred_instance['name']}...")
        if self._start_instance(self.preferred_instance):
            self.active_instance = self.preferred_instance["name"]
            self.active_zone = self.preferred_instance["zone"]
            self.bootstrap_v18(is_prebaked=True)
            return self.get_ip()

        # 3. GLOBAL SPAWN (Criar nova máquina da Imagem Gold se tudo falhar ou estiver ocupado)
        for zone in self.failover_zones:
            new_name = f"lana-engine-spawn-{int(time.time())}"
            print(f"[FAILOVER] Tentando Spawn Industrial em {zone} usando Gold Image...")
            if self._create_from_gold(new_name, zone):
                self.active_instance = new_name
                self.active_zone = zone
                self.bootstrap_v18(is_prebaked=True)
                return self.get_ip()

        raise Exception("CATÁSTROFE: Nenhuma GPU disponível no GCP US!")

    def _start_instance(self, inst):
        cmd = ["gcloud", "compute", "instances", "start", inst["name"], 
               "--project", self.project_id, "--zone", inst["zone"], "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return res.returncode == 0

    def _create_from_gold(self, name, zone):
        """Cria uma máquina G2 (L4) instantaneamente a partir da imagem Gold."""
        cmd = [
            "gcloud", "compute", "instances", "create", name,
            "--project", self.project_id, "--zone", zone,
            "--machine-type=g2-standard-4",
            "--accelerator=type=nvidia-l4,count=1",
            "--image", GOLD_IMAGE,
            "--boot-disk-size=100GB",
            "--disk=name=lana-weights-v1,mode=ro,device-name=weights-disk",
            "--maintenance-policy=TERMINATE",
            "--quiet"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return res.returncode == 0

    def bootstrap_v18(self, is_prebaked=False):
        """Injeta patches e inicia o motor com auto-cura V18.11."""
        print(f"[V18] Configurando motor em {self.active_instance} (Failover Mode)...")
        
        # 0. Garantir Permissões e Montar Disco Gold (Zero Cold Start)
        init_cmd = ["gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                    "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                    "sudo mkdir -p /workspace /mnt/weights && sudo chmod 777 /workspace && "
                    "sudo mount -o discard,defaults /dev/disk/by-id/google-weights-disk /mnt/weights || true && "
                    "gcloud auth configure-docker us-east1-docker.pkg.dev --quiet", 
                    "--quiet"]
        subprocess.run(init_cmd, shell=True)

        # 1. Sincronizar Scripts e Patches
        sync_files = ["lipsync_pipeline.py", "industrial_main.py", "boot_industrial_v18.sh", "Dockerfile.v8_industrial", "requirements.txt"]
        for file in sync_files:
            scp_cmd = ["gcloud", "compute", "scp", file, 
                       f"{self.active_instance}:/workspace/", "--project", self.project_id, 
                       "--zone", self.active_zone, "--tunnel-through-iap", "--quiet"]
            
            connected = False
            for i in range(3):
                res = subprocess.run(scp_cmd, shell=True)
                if res.returncode == 0:
                    connected = True
                    break
                time.sleep(5)
            if not connected: raise Exception(f"Erro ao sincronizar {file}")

        # 2. Iniciar Motor via Script Industrial (Com Watchdog)
        ssh_cmd = ["gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                    "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                    "sudo touch /tmp/lana_maestro.lock; "
                    "sudo cp /workspace/lipsync_pipeline.py /workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py; "
                    "bash /workspace/boot_industrial_v18.sh; "
                    "sudo rm /tmp/lana_maestro.lock", 
                    "--quiet"]
        subprocess.run(ssh_cmd, shell=True)
        print("[V18] Motor Acoplado via Industrial Boot Script.")

    def get_ip(self):
        cmd = ["gcloud", "compute", "instances", "describe", self.active_instance, 
               "--project", self.project_id, "--zone", self.active_zone, 
               "--format=get(networkInterfaces[0].accessConfigs[0].natIP)"]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip()

    def stop_engine(self):
        """Para a instancia GCP (Resiliência: Mantém ligada se falhou para debug)."""
        if not self.active_instance: return
        print(f"[MAESTRO] O motor {self.active_instance} permanecerá ativo para o ciclo de watchdog v2.")

    def upload_assets(self, local_path):
        filename = os.path.basename(local_path)
        gcs_path = f"gs://{BUCKET_NAME}/temp/{filename}"
        print(f"[GCS] Sincronizando: {gcs_path}")
        subprocess.run(["gsutil", "cp", local_path, gcs_path], capture_output=True, shell=True)
        return gcs_path

    def download_result(self, job_id, local_folder="c:/Users/vinic/workspace_antigravity/Avatar/outputs"):
        filename = f"final_{job_id}.mp4"
        gcs_path = f"gs://{BUCKET_NAME}/outputs/{filename}"
        local_path = os.path.join(local_folder, filename)
        if not os.path.exists(local_folder): os.makedirs(local_folder)
        print(f"[GCS] Download Final: {local_path}...")
        subprocess.run(["gsutil", "cp", gcs_path, local_path], shell=True, capture_output=True)
        return local_path

class AgenteLanaOrchestrator:
    """Orquestrador V16 (Smart Maestro): Resiliência, Autocorreção e Orçamento Inteligente."""
    
    def __init__(self):
        self.engine = LanaIndustrialEngine()

    def generate_audio(self, text, output_path="c:/Users/vinic/workspace_antigravity/Avatar/temp_audio.mp3"):
        print(f"[TTS] Gerando Sarah (Brazil Identity) para: '{text[:50]}...'")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.50, "similarity_boost": 0.80}
        }
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200:
            with open(output_path, 'wb') as f: f.write(res.content)
            # Aceleração Padrão Industrial
            fast_path = output_path.replace(".mp3", "_fast.mp3")
            subprocess.run(["ffmpeg", "-y", "-i", output_path, "-filter:a", "atempo=1.12", fast_path], capture_output=True)
            if os.path.exists(fast_path): os.replace(fast_path, output_path)
            return output_path
        raise Exception(f"Erro ElevenLabs: {res.text}")

    def produce_video_from_text(self, text):
        start_time = time.time()
        print(f"[MAESTRO] Iniciando Ciclo V18 para: {text[:50]}...")
        
        try:
            # 1. Áudio
            audio_local = self.generate_audio(text)
            
            # Configurações Industriais L4 + Spot
            machine_type = "g2-standard-4"  # Nvidia L4 (Melhor custo/benefício que T4)
            image_uri = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0"
            
            # 2. Infra Inteligente
            vm_ip = self.engine.ensure_instance_ready()
            gcs_path = self.engine.upload_assets(audio_local)
            public_url = gcs_path.replace("gs://", "https://storage.googleapis.com/")
            
            # 3. Render API Polling
            payload = {
                "presenter_id": "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ",
                "script": {"type": "audio", "audio_url": public_url}
            }
            
            job_id = None
            print("[POLLING] Acoplando Motor Industrial...")
            for i in range(45): # Até 7.5 min total (Boot + Cold Start Docker)
                try:
                    res = requests.post(f"http://{vm_ip}:8080/clips", json=payload, timeout=5)
                    if res.status_code == 200:
                        job_id = res.json().get("id")
                        print(f"\n[AVATAR] Motor Acoplado! Job ID: {job_id}")
                        break
                    
                    # Status de espera industrial
                    progress = (i + 1) / 45
                    bar = "█" * int(20 * progress) + "░" * (20 - int(20 * progress))
                    print(f" [POLLING] Aquecendo Motores GPU: |{bar}| {int(progress*100)}%...", end="\r")
                except:
                    print(f" [POLLING] Sincronia de Rede ({i+1}/45)...", end="\r")
                time.sleep(10) # Intervalo requisitado de 10 segundos
            
            if not job_id: raise Exception("Motor não responde.")

            # 4. Monitoramento com Barra de Progresso (V18.2)
            print("\n[PROGRESSO] Renderizando Video HQ:")
            for i in range(120): # 30 min max para HQ Restorer
                try:
                    time.sleep(10)
                    r_status = requests.get(f"http://{vm_ip}:8080/clips/{job_id}", timeout=10)
                    if r_status.status_code == 200:
                        data = r_status.json()
                        status = data.get("status")
                        
                        # Barra de Progresso Visual
                        progress = i / 120
                        bar_len = 30
                        filled = int(bar_len * progress)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        print(f" |{bar}| {int(progress*100)}% - [{status.upper()}]", end="\r")

                        if status == "completed":
                            print(f"\n[SUCESSO] Produção HQ Finalizada.")
                            local_video = self.engine.download_result(job_id)
                            duration = time.time() - start_time
                            print(f"[FINAL] Lana entregue em: {local_video} ({duration/60:.2f} min)")
                            return {"status": "success", "video_path": local_video}
                        elif status == "failed":
                            raise Exception(f"ERRO MOTOR: {data.get('error')}")
                    else:
                        print(f" [RECONECTANDO] API Status: {r_status.status_code}...", end="\r")
                except Exception as e:
                    print(f" [AGUARDANDO] Sincronia de Rede...          ", end="\r")
                    time.sleep(5)
            
            raise Exception("Timeout na produção HQ.")

        except Exception as e:
            print(f"[CRITICAL] Falha no Maestro: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    maestro = AgenteLanaOrchestrator()
    maestro.produce_video_from_text("O pipeline V17 Zero Crash está agora operacional. Blindagem de memória e orquestração inteligente ativadas.")
