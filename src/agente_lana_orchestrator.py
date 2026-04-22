import os
import time
import requests
import subprocess
import json
import sqlite3
from datetime import datetime
from agno.agent import Agent
from google.cloud import storage
from secrets_manager import get_secret

# --- CONFIGURAÇÕES SOBERANAS (PROJETO AVATAR) ---
PROJECT_ID = get_secret("GOOGLE_CLOUD_PROJECT", fallback_env="brasili-ia-news")
BUCKET_NAME = get_secret("GCS_VAULT_BUCKET", fallback_env="brasil-ai-avatars-vault")
INSTANCE_NAME = "lana-engine-cris-v3-soberana"
ZONE = "us-west1-a"
GOLD_IMAGE = "projects/brasili-ia-news/global/images/lana-v6-industrial-v1"
ELEVENLABS_API_KEY = get_secret("ELEVEN_LABS_API_KEY")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Sarah (Official Project Standard)

class LanaIndustrialEngine:
    """Ferramentas de infraestrutura GCP com Inteligência Maestro V18 (Gold Standard)."""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.preferred_instance = {"name": INSTANCE_NAME, "zone": ZONE, "type": "L4"}
        self.failover_zones = [
            "us-central1-a", "us-east1-c", "us-east4-a", "us-west1-a", 
            "europe-west4-a", "europe-west1-b", "asia-northeast1-a"
        ]
        self.active_instance = None
        self.active_zone = None

    def _test_ssh(self, name, zone, max_retries=3):
        print(f"[MAESTRO] Testando conexão SSH com {name} em {zone}...")
        for i in range(max_retries):
            cmd = ["gcloud", "compute", "ssh", name, "--project", self.project_id,
                   "--zone", zone, "--tunnel-through-iap", "--command", "echo 'SSH OK'", "--quiet"]
            res = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)
            if res.returncode == 0 and "SSH OK" in res.stdout:
                print(f"[MAESTRO] SSH estabelecido com {name}.")
                return True
            time.sleep(15)
        print(f"[ERROR] Falha de SSH com {name} após várias tentativas.")
        return False

    def _find_existing_engine(self):
        """Busca por uma instância industrial já em execução para evitar cold-start."""
        print("[MAESTRO] Buscando motores ativos no GCP...")
        cmd = ["gcloud", "compute", "instances", "list", 
               f"--filter=name~lana-engine-spawn- AND status=RUNNING", 
               "--format=json", "--project", self.project_id]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            instances = json.loads(res.stdout)
            if instances:
                # Retorna a mais recente
                inst = sorted(instances, key=lambda x: x['name'], reverse=True)[0]
                print(f"[REUSE] Motor detectado: {inst['name']} em {inst['zone'].split('/')[-1]}")
                return inst['name'], inst['zone'].split('/')[-1]
        return None, None

    def ensure_instance_ready(self):
        """Garante uma máquina pronta, reusando ativas ou criando novas via Gold Image."""
        
        # 1. Tentar REUSO (Objetivo: Velocidade Sequencial)
        existing_name, existing_zone = self._find_existing_engine()
        if existing_name:
            if self._test_ssh(existing_name, existing_zone):
                self.active_instance = existing_name
                self.active_zone = existing_zone
                print(f"[SUCCESS] Reusando motor aquecido: {self.active_instance}")
                self.heartbeat() # Pulso de vida ao reusar
                # Verificar se o servidor MCP está rodando
                check_mcp = self.call_mcp_tool("ping")
                if not check_mcp or "error" in check_mcp:
                    print("[REUSE] Servidor MCP inativo. Reiniciando Bootstrap...")
                    self.bootstrap_v18(is_prebaked=True)
                return self.get_ip()
            else:
                print(f"[WARNING] Motor {existing_name} falhou no teste de vida. Purgando...")
                self._purge_zone(existing_name, existing_zone)

        # 2. GLOBAL SPAWN (Criar nova máquina - Fallback)
        for zone in self.failover_zones:
            new_name = f"lana-engine-spawn-{int(time.time())}"
            print(f"[FAILOVER] Tentando Spawn Industrial em {zone} usando Gold Image...")
            if self._create_from_gold(new_name, zone):
                if self._test_ssh(new_name, zone, max_retries=3):
                    self.active_instance = new_name
                    self.active_zone = zone
                    try:
                        self.bootstrap_v18(is_prebaked=True)
                        self.heartbeat() # Primeiro pulso
                        return self.get_ip()
                    except Exception as e:
                        print(f"[ERROR] Bootstrap falhou no Spawn em {zone}: {e}")
                        self._purge_zone(new_name, zone)
                else:
                    print(f"[ERROR] Máquina spawnada {new_name} em {zone} não respondeu SSH. Iniciando Purga...")
                    self._purge_zone(new_name, zone)
            else:
                print(f"[FAILOVER] Falha no spawn na zona {zone}. Garantindo limpeza...")
                self._purge_zone(new_name, zone)

        raise Exception("CATÁSTROFE: Nenhuma GPU disponível no GCP Global!")

    def _purge_zone(self, name, zone):
        """Purga absoluta de qualquer recurso na região para garantir Zero-Waste."""
        print(f"[ZERO-WASTE] Purgando {name} em {zone}...")
        subprocess.run(f"gcloud compute instances delete {name} --project {self.project_id} --zone {zone} --delete-disks=all --quiet 2>/dev/null", shell=True)
        # Tentar deletar disco avulso caso a instancia não tenha sido criada mas o disco sim
        subprocess.run(f"gcloud compute disks delete {name} --project {self.project_id} --zone {zone} --quiet 2>/dev/null", shell=True)

    def _start_instance(self, inst):
        cmd = ["gcloud", "compute", "instances", "start", inst["name"], 
               "--project", self.project_id, "--zone", inst["zone"], "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return res.returncode == 0

    def _create_from_gold(self, name, zone):
        """Cria uma máquina G2 (L4) STANDARD (Sem preempção)."""
        cmd = [
            "gcloud", "compute", "instances", "create", name,
            "--project", self.project_id, "--zone", zone,
            "--machine-type=g2-standard-12",
            "--image", GOLD_IMAGE,
            "--boot-disk-size=100GB",
            "--provisioning-model=STANDARD",
            "--maintenance-policy=TERMINATE",
            "--quiet"
        ]
        res = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
        if res.returncode != 0:
            print(f"[ERROR] Falha ao criar na zona {zone}: {res.stderr}")
        return res.returncode == 0

    def call_mcp_tool(self, method, params=None):
        """Informa ferramentas via MCP Bridge (SSH Stdio). Resiliência Total."""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": int(time.time())
        }
        json_req = json.dumps(request)
        
        # Comando que injeta o request no stdin do servidor remoto
        ssh_cmd = ["gcloud", "compute", "ssh", self.active_instance, 
                   "--project", self.project_id, "--zone", self.active_zone, 
                   "--tunnel-through-iap", "--quiet", "--command", 
                   f"echo '{json_req}' | python3 /workspace/lana_mcp_server.py"]
        
        res = subprocess.run(ssh_cmd, capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            try:
                # Filtrar apenas a linha que é JSON (ignorando possíveis logs no stderr que venham misturados se não houver stream separado)
                for line in res.stdout.splitlines():
                    if '{"jsonrpc":' in line:
                        return json.loads(line).get("result")
            except: pass
        return {"error": "MCP Bridge Failure"}

    def bootstrap_v18(self, is_prebaked=False):
        """Injeta patches e inicia o motor com auto-cura V18.11."""
        print(f"[V18] Configurando motor em {self.active_instance} (MCP Mode)...")
        
        # 0. Garantir Permissões e Montar Disco Gold
        init_cmd = ["gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                    "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                    "sudo mkdir -p /workspace && sudo chmod 777 /workspace && "
                    "sudo gcloud auth configure-docker us-east1-docker.pkg.dev --quiet", 
                    "--quiet"]
        
        for i in range(5):
            res = subprocess.run(init_cmd, shell=True)
            if res.returncode == 0: break
            time.sleep(15)
        else:
            raise Exception("Falha no setup inicial (mkdir, chmod, docker auth)")

        # 1. Sincronizar Scripts (Incluindo o novo MCP Server)
        # Mapeamento: {Arquivo Local: Destino Remoto}
        sync_files = {
            "src/lipsync_pipeline.py": "/workspace/lipsync_pipeline.py",
            "src/industrial_main.py": "/workspace/industrial_main.py",
            "infra/boot_industrial_v18.sh": "/workspace/boot_industrial_v18.sh",
            "infra/Dockerfile": "/workspace/Dockerfile",
            "infra/requirements.txt": "/workspace/requirements.txt",
            "src/lana_mcp_server.py": "/workspace/lana_mcp_server.py"
        }
        
        for local_file, remote_file in sync_files.items():
            scp_cmd = ["gcloud", "compute", "scp", local_file, 
                       f"{self.active_instance}:{remote_file}", "--project", self.project_id, 
                       "--zone", self.active_zone, "--tunnel-through-iap", "--quiet"]
            res = subprocess.run(scp_cmd, shell=True)
            if res.returncode != 0:
                raise Exception(f"Falha ao copiar script essencial: {local_file}")

        # 2. Iniciar Motor e MCP Bridge
        ssh_cmd = ["gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                    "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                    "sudo cp /workspace/lipsync_pipeline.py /workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py; "
                    "bash /workspace/boot_industrial_v18.sh", 
                    "--quiet"]
        res = subprocess.run(ssh_cmd, shell=True)
        if res.returncode != 0:
            raise Exception("Falha ao iniciar Motor e MCP Bridge (boot_industrial_v18.sh)")
        print("[V18] Motor e MCP Bridge prontos.")

    def get_ip(self):
        cmd = ["gcloud", "compute", "instances", "describe", self.active_instance, 
               "--project", self.project_id, "--zone", self.active_zone, 
               "--format=get(networkInterfaces[0].accessConfigs[0].natIP)"]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip()

    def heartbeat(self):
        """Envia um pulso de vida para o Sentinela remoto não desligar a máquina."""
        if not self.active_instance: return
        cmd = ["gcloud", "compute", "ssh", self.active_instance, 
               "--project", self.project_id, "--zone", self.active_zone, 
               "--tunnel-through-iap", "--quiet", "--command", 
               "touch /workspace/heartbeat"]
        subprocess.run(cmd, shell=True, capture_output=True)

    def stop_engine(self):
        """Libera a instância para o ciclo de ociosidade (Zero-Waste Heartbeat)."""
        if not self.active_instance: return
        print(f"[FINOPS] Job finalizado. Motor {self.active_instance} entra em modo de espera (15min grace period).")

    def upload_assets(self, local_path):
        filename = os.path.basename(local_path)
        gcs_path = f"gs://{BUCKET_NAME}/temp/{filename}"
        print(f"[GCS] Sincronizando: {gcs_path}")
        subprocess.run(["gsutil", "cp", local_path, gcs_path], capture_output=True, shell=True)
        self.heartbeat() # Atividade detectada
        return gcs_path

    def download_result(self, job_id, local_folder="c:/Users/vinic/workspace_antigravity/Avatar/outputs"):
        now = datetime.now()
        timestamp = now.strftime("%d_%m_%Y_%H_%M_%S")
        filename = f"lana_{timestamp}_{job_id}.mp4"
        gcs_path = f"gs://{BUCKET_NAME}/outputs/final_{job_id}.mp4"
        local_path = os.path.abspath(os.path.join(local_folder, filename))
        if not os.path.exists(local_folder): os.makedirs(local_folder)
        print(f"[GCS] Download Final: {local_path}...")
        subprocess.run(["gsutil", "cp", gcs_path, local_path], shell=True, capture_output=True)
        self.heartbeat() # Pulso final de entrega
        print(f"[SUCCESS] Video entregue localmente em: {local_path}")
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
            "voice_settings": {
                "stability": 0.40, 
                "similarity_boost": 0.90,
                "style": 0.20,
                "use_speaker_boost": True
            }
        }
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200:
            with open(output_path, 'wb') as f: f.write(res.content)
            # Aceleração Padrão Industrial (Aumentado para 1.18x para remover tom lento)
            fast_path = output_path.replace(".mp3", "_fast.mp3")
            subprocess.run(["ffmpeg", "-y", "-i", output_path, "-filter:a", "atempo=1.18", fast_path], capture_output=True)
            if os.path.exists(fast_path): os.replace(fast_path, output_path)
            return output_path
        raise Exception(f"Erro ElevenLabs: {res.text}")

    def criar_avatar(self, audio_path, video_ref_path=None):
        """Cria o avatar usando a ponte MCP (Zero-Waste & Portless)."""
        # 1. Upload do Áudio para o GCS
        gcs_path = self.engine.upload_assets(audio_path)
        public_url = gcs_path.replace("gs://", "https://storage.googleapis.com/")
        
        # 2. Criar Job via MCP
        print("[MAESTRO] Enviando Job de Renderização via MCP Bridge...")
        job_res = self.engine.call_mcp_tool("create_render_job", {
            "audio_url": public_url,
            "presenter_id": "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"
        })
        
        if not job_res or "error" in job_res:
            raise Exception(f"Falha ao criar job MCP: {job_res}")
            
        job_id = job_res.get("id")
        print(f"[MAESTRO] Job Criado: {job_id}")
        
        # 3. Polling via MCP
        print("[MAESTRO] Monitorando progresso via MCP...")
        for i in range(120): # 20 minutos max
            time.sleep(10)
            status_res = self.engine.call_mcp_tool("get_render_status", {"job_id": job_id})
            
            if not status_res or "error" in status_res:
                print(f" [AVISO] Falha na sincronia MCP ({i+1}/120)...", end="\r")
                continue
                
            status = status_res.get("status")
            
            # Barra de Progresso Visual
            progress = (i + 1) / 120
            bar_len = 30
            filled = int(bar_len * progress)
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f" [PROGRESSO] |{bar}| {int(progress*100)}% - [{status.upper()}]", end="\r")
            
            if status == "completed":
                print("\n[SUCESSO] Renderização finalizada!")
                self.engine.heartbeat() # Pulso final após sucesso
                local_video = self.engine.download_result(job_id)
                return local_video
            elif status == "failed":
                raise Exception(f"Job falhou no motor: {status_res.get('error')}")
                
        raise Exception("Timeout na renderização via MCP.")

    def produce_video_from_text(self, text):
        """Workflow unificado de alto nível."""
        try:
            # Garante infra
            self.engine.ensure_instance_ready()
            
            # Gera audio
            audio_path = self.generate_audio(text)
            
            # Cria avatar
            video_path = self.criar_avatar(audio_path)
            
            return {"status": "success", "video_path": video_path}
        except Exception as e:
            print(f"[CRITICAL] Falha na Produção: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    maestro = AgenteLanaOrchestrator()
    maestro.produce_video_from_text("O pipeline V17 Zero Crash está agora operacional. Blindagem de memória e orquestração inteligente ativadas.")
