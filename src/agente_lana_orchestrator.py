import base64
import os
import time
import requests
import subprocess
import json
import sys
import sqlite3
import zipfile
from datetime import datetime
from agno.agent import Agent
from google.cloud import storage
from secrets_manager import get_secret

# --- CONFIGURAÇÕES SOBERANAS (PROJETO AVATAR) ---
PROJECT_ID = get_secret("GOOGLE_CLOUD_PROJECT", fallback="brasili-ia-news")
BUCKET_NAME = get_secret("GCS_VAULT_BUCKET", fallback="brasil-ai-avatars-vault")

# TIER 1: NVIDIA L4 (Premium Performance)
L4_IMAGE_FAMILY = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
L4_MACHINE = "g2-standard-12"

ELEVENLABS_API_KEY = get_secret("ELEVEN_LABS_API_KEY")
VOICE_ID = "XrExE9yKIg1WjnnlVkGX" # Sarah Customizada ElevenLabs (Reference p_5125)
DOCKER_IMAGE = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.7"

class LanaIndustrialEngine:
    """Ferramentas de infraestrutura GCP com Inteligência Maestro V18 (Gold Standard)."""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.l4_zones = [
            "us-east1-c", "us-west4-a", "us-east1-d", "us-east4-a", "us-west1-a", 
            "us-central1-a", "us-east5-a", "us-south1-a", "europe-west4-a", "europe-west1-b",
            "europe-west6-b", "asia-east1-a", "northamerica-northeast1-b"
        ]
        self.active_instance = None
        self.active_zone = None
        self.current_gpu_type = "L4"

    def _run_ssh_cmd(self, cmd_list, use_y=True, capture=True):
        """Helper robusto para rodar comandos via gcloud compute ssh no Windows/Plink."""
        # Se for uma lista, junta com espaço.
        if isinstance(cmd_list, list):
            cmd_str = " ".join(cmd_list)
        else:
            cmd_str = cmd_list
            
        final_cmd = f"echo y | {cmd_str}" if use_y else cmd_str
        res = subprocess.run(final_cmd, shell=True, capture_output=capture, text=True, encoding='utf-8', errors='ignore')
        return res

    def _test_ssh(self, name, zone, max_retries=15, progress_callback=None):
        print(f"[MAESTRO] Testando conexão SSH com {name} em {zone}...")
        for i in range(max_retries):
            if progress_callback:
                progress_callback(f"Teste SSH ({i+1}/{max_retries})...")
            cmd = ["gcloud", "compute", "ssh", name, "--project", self.project_id,
                   "--zone", zone, "--tunnel-through-iap", "--command", "\"echo SSH_OK\"", "--quiet"]
            
            res = self._run_ssh_cmd(cmd)
            if res.returncode == 0 and "SSH_OK" in res.stdout:
                print(f"[MAESTRO] SSH estabelecido com {name}.")
                return True
            else:
                print(f"[DEBUG] SSH Fail: code={res.returncode}, out='{res.stdout.strip()}', err='{res.stderr.strip()}'")
            time.sleep(10)
        print(f"[ERROR] Falha de SSH com {name} após várias tentativas.")
        return False

    def _find_existing_engine(self):
        """Busca por uma instância industrial já em execução para evitar cold-start."""
        print("[MAESTRO] Buscando motores ativos no GCP...")
        cmd = ["gcloud", "compute", "instances", "list", 
               f"--filter=name~lana-engine- AND status=RUNNING", 
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

    def ensure_instance_ready(self, progress_callback=None, force_gpu="ALL"):
        """Garante uma máquina pronta, utilizando exclusivamente NVIDIA L4."""
        
        # 1. Tentar REUSO (Objetivo: Velocidade Sequencial)
        existing_name, existing_zone = self._find_existing_engine()
        if existing_name:
            if self._test_ssh(existing_name, existing_zone, progress_callback=progress_callback):
                # Validar se o motor existente é do tipo solicitado
                # (Simplificação: se for reuse, assume L4 ou o que estiver lá)
                self.active_instance = existing_name
                self.active_zone = existing_zone
                if progress_callback: progress_callback("Reusando motor aquecido.")
                self.start_heartbeat()
                self._ensure_server_running()
                return self.get_ip()
            else:
                self._purge_zone(existing_name, existing_zone)

        # 1. TIER 1: NVIDIA L4 (Prioridade Absoluta)
        print("[MAESTRO] Buscando disponibilidade de NVIDIA L4 (Arquitetura 4)...")
        for zone in self.l4_zones:
            new_name = f"lana-engine-l4-{int(time.time())}"
            if progress_callback: progress_callback(f"L4 Spawn em {zone}...")
            
            # Loop de tentativa com inteligência de cota
            for attempt in range(2):
                success, error_msg = self._create_gpu_instance(new_name, zone)
                if success:
                    if self._test_ssh(new_name, zone, max_retries=15, progress_callback=progress_callback):
                        self.active_instance = new_name
                        self.active_zone = zone
                        self.current_gpu_type = "L4"
                        self.start_heartbeat()
                        self.bootstrap_v18(is_prebaked=True)
                        return self.get_ip()
                    self._purge_zone(new_name, zone)
                    break # Pula para a próxima zona se o SSH falhou
                
                if "Quota" in error_msg or "GPUS_ALL_REGIONS" in error_msg:
                    print(f"[QUOTA] Cota de 1.0 GPU ocupada. Aguardando 60s para liberação (Tentativa {attempt+1}/2)...")
                    time.sleep(60)
                    continue
                else:
                    # Se for erro de estoque (Stockout), pula direto para próxima zona
                    break

        raise Exception("CATÁSTROFE: Nenhuma GPU L4 disponível ou Cota Global Excedida!")

    def _purge_zone(self, name, zone):
        """Purga absoluta de qualquer recurso na região para garantir Zero-Waste."""
        print(f"[ZERO-WASTE] Purgando {name} em {zone}...")
        subprocess.run(f"gcloud compute instances delete {name} --project {self.project_id} --zone {zone} --delete-disks=all --quiet 2>NUL", shell=True)
        # Tentar deletar disco avulso caso a instancia não tenha sido criada mas o disco sim
        subprocess.run(f"gcloud compute disks delete {name} --project {self.project_id} --zone {zone} --quiet 2>NUL", shell=True)

    def _start_instance(self, inst):
        cmd = ["gcloud", "compute", "instances", "start", inst["name"], 
               "--project", self.project_id, "--zone", inst["zone"], "--quiet"]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return res.returncode == 0

    def _create_gpu_instance(self, name, zone):
        """Cria uma instância L4 usando Arquitetura 4 (Nativa + Startup Script)."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        startup_script_path = os.path.join(base_dir, "infra", "startup_arch4.sh")
        
        cmd = [
            "gcloud", "compute", "instances", "create", name,
            "--project", self.project_id, "--zone", zone,
            f"--machine-type={L4_MACHINE}",
            f"--image-family=common-cu129-ubuntu-2204-nvidia-580",
            f"--image-project=deeplearning-platform-release",
            "--accelerator=type=nvidia-l4,count=1",
            "--boot-disk-size=150GB",
            "--provisioning-model=STANDARD",
            "--maintenance-policy=TERMINATE",
            f"--metadata-from-file=startup-script={startup_script_path}",
            "--scopes=cloud-platform", # Essencial para GCS Fuse e Artifact Registry
            "--quiet"
        ]
            
        res = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
        if res.returncode != 0:
            print(f"[ERROR] Failover em {zone}: {res.stderr}")
            return False, res.stderr
        return True, ""

    def call_mcp_tool(self, method, params=None):
        """Informa ferramentas via MCP Bridge (HTTP Mode). Estabilidade Industrial."""
        for attempt in range(3):
            try:
                res = self._run_http_mcp_command(method, params)
                if res and "error" not in res and "detail" not in res:
                    return res
                err_msg = res.get('error') or res.get('detail') if res else 'Vazio'
                print(f"[MAESTRO] Tentativa {attempt+1} falhou: {err_msg}")
            except Exception as e:
                print(f"[MAESTRO] Erro na tentativa {attempt+1}: {e}")
            
            if attempt == 0: # Se a primeira falhar, garante que o motor está ok
                self._ensure_server_running()
            time.sleep(5)
        
        return {"error": "MCP Bridge Failure: Todas as tentativas falharam."}

    def _run_http_mcp_command(self, method, params):
        """Faz a chamada HTTP para o container via SSH Tunnel."""
        # Mapeamento de métodos MCP para Endpoints HTTP
        if method == "create_render_job":
            http_method = "POST"
            url = "http://localhost:8080/clips"
            # Formato DIDClipRequest para industrial_main.py
            did_payload = {
                "presenter_id": params.get("presenter_id", "default"),
                "script": {
                    "type": "audio",
                    "audio_url": params.get("audio_url")
                }
            }
            data_payload = json.dumps(did_payload)
        elif method == "get_render_status":
            http_method = "GET"
            job_id = params.get("job_id")
            url = f"http://localhost:8080/clips/{job_id}"
            data_payload = None
        else:
            return {"error": f"Método {method} não suportado via HTTP."}
        
        # Construir o comando curl (usando base64 para evitar problemas de escaping)
        if http_method == "POST":
            import base64
            b64_payload = base64.b64encode(data_payload.encode()).decode()
            curl_cmd = f"echo {b64_payload} | base64 -d | curl -s -X POST {url} -H 'Content-Type: application/json' -d @-"
        else:
            curl_cmd = f"curl -s {url}"

        cmd = [
            "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
            "--zone", self.active_zone, "--tunnel-through-iap", "--command",
            f"\"{curl_cmd}\"",
            "--quiet"
        ]
        
        res = self._run_ssh_cmd(cmd)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except Exception as e:
                return {"error": f"JSON Parse Error: {e} | Raw: {res.stdout[:100]}"}
        return {"error": f"Curl Exit Code: {res.returncode}"}

    def _ensure_server_running(self):
        """Garante que o container e o servidor MCP estão operacionais."""
        print(f"[AGNO] Validando integridade do Motor em {self.active_instance}...")
        
        # 1. Verificar se o container existe
        check_cmd = [
            "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
            "--zone", self.active_zone, "--tunnel-through-iap", "--command",
            "\"sudo docker inspect -f '{{.State.Running}}' lana-engine 2>/dev/null\"",
            "--quiet"
        ]
        res = self._run_ssh_cmd(check_cmd)
        
        DOCKER_IMAGE = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.7"
        if res.returncode != 0 or "true" not in res.stdout.lower():
            print(f"[AGNO] Container não encontrado. Criando container passivo...")
            # Auto-criar o container passivo
            run_cmd = [
                "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                f"\"sudo docker rm -f lana-engine 2>/dev/null; "
                f"sudo gcloud auth configure-docker us-east1-docker.pkg.dev --quiet; "
                f"sudo docker pull {DOCKER_IMAGE}; "
                f"sudo docker run -d --name lana-engine --gpus all --network host "
                f"-v /workspace:/workspace -v /mnt/weights:/mnt/weights "
                f"{DOCKER_IMAGE} tail -f /dev/null\"",
                "--quiet"
            ]
            self._run_ssh_cmd(run_cmd)

        # 2. Health Check do Servidor MCP
        health_cmd = [
            "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
            "--zone", self.active_zone, "--tunnel-through-iap", "--command",
            "\"curl -s --connect-timeout 2 http://localhost:8080/clips > /dev/null && echo 'OK'\"",
            "--quiet"
        ]
        health_res = self._run_ssh_cmd(health_cmd)
        if "OK" in health_res.stdout:
            print(f"[AGNO] Motor e Servidor MCP operacionais.")
            return

        # 3. Reanimação: Buscar scripts do GCS + Iniciar Servidor
        GCS_SCRIPTS = "gs://brasil-ai-avatars-vault/scripts"
        
        print(f"[AGNO] Sincronizando scripts do GCS...")
        sync_cmd = [
            "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
            "--zone", self.active_zone, "--tunnel-through-iap", "--command",
            f"\"mkdir -p /workspace/src && "
            f"gsutil -m cp {GCS_SCRIPTS}/* /workspace/ && "
            f"cp /workspace/industrial_main.py /workspace/src/industrial_main.py && "
            f"cp /workspace/lipsync_pipeline.py /workspace/src/lipsync_pipeline.py\"",
            "--quiet"
        ]
        self._run_ssh_cmd(sync_cmd)

        print(f"[AGNO] Iniciando Servidor MCP (FastAPI)...")
        exec_cmd = [
            "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
            "--zone", self.active_zone, "--tunnel-through-iap", "--command",
            "\"sudo docker exec -d lana-engine python3 /workspace/src/industrial_main.py\"",
            "--quiet"
        ]
        self._run_ssh_cmd(exec_cmd)
        time.sleep(8)
        print("[AGNO] Motor e Servidor MCP acionados.")

    def bootstrap_v18(self, is_prebaked=False):
        """Bootstrap Industrial v18 — 100% GCS-Native + LatentSync Setup. Zero dependências locais."""
        GCS_SCRIPTS = "gs://brasil-ai-avatars-vault/scripts"
        DOCKER_IMAGE = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.7"
        
        def _ssh(cmd_str, label="CMD"):
            """Helper para executar SSH com retry."""
            cmd = [
                "gcloud", "compute", "ssh", self.active_instance, "--project", self.project_id,
                "--zone", self.active_zone, "--tunnel-through-iap", "--command",
                f"\"{cmd_str}\"", "--quiet"
            ]
            res = self._run_ssh_cmd(cmd)
            if res.returncode != 0:
                print(f"[AGNO] WARN {label}: {res.stderr[:200]}")
            return res
        
        # 1. Preparar filesystem + Auth Docker
        print("[AGNO] [1/7] Preparando filesystem na VM...")
        for i in range(5):
            res = _ssh("sudo mkdir -p /workspace/src /workspace/outputs/temp && "
                       "sudo chmod -R 777 /workspace && "
                       "sudo gcloud auth configure-docker us-east1-docker.pkg.dev --quiet", "PREP")
            if res.returncode == 0: break
            time.sleep(15)
        else:
            raise Exception(f"Falha no setup inicial: {res.stderr}")

        # 2. Clonar LatentSync (se não existir)
        print("[AGNO] [2/7] Restaurando LatentSync...")
        _ssh("if [ ! -d /workspace/latentsync ]; then "
             "git clone https://github.com/bytedance/LatentSync /workspace/latentsync && "
             "chmod -R 777 /workspace/latentsync; "
             "else echo 'LatentSync já presente'; fi", "GIT")

        # 3. Sincronizar Assets (vídeos base dos avatares)
        print("[AGNO] [3/7] Sincronizando Assets de Avatares...")
        _ssh("mkdir -p /workspace/latentsync/assets && "
             "gsutil -m cp gs://lana-weights-universal/assets/*.mp4 /workspace/latentsync/assets/ 2>/dev/null || "
             "echo 'Assets já sincronizados ou bucket indisponível'", "ASSETS")

        # 4. Mapear Checkpoints (symlinks para /mnt/weights)
        print("[AGNO] [4/7] Mapeando Checkpoints Industriais...")
        _ssh("rm -rf /workspace/latentsync/checkpoints && "
             "ln -sfn /mnt/weights /workspace/latentsync/checkpoints && "
             "mkdir -p /workspace/latentsync/checkpoints/gfpgan && "
             "ln -sfn /mnt/weights/gfpgan/GFPGANv1.4.pth /workspace/latentsync/checkpoints/gfpgan/GFPGANv1.4.pth && "
             "chmod -R 777 /workspace/latentsync/checkpoints", "CHECKPOINTS")

        # 5. Sincronizar Scripts do GCS + Aplicar Patches
        print("[AGNO] [5/7] Sincronizando scripts e patches...")
        _ssh(f"gsutil -m cp {GCS_SCRIPTS}/* /workspace/ && "
             "cp /workspace/industrial_main.py /workspace/src/industrial_main.py && "
             "cp /workspace/lipsync_pipeline.py /workspace/src/lipsync_pipeline.py && "
             "cp /workspace/industrial_main.py /workspace/latentsync/industrial_main.py && "
             "mkdir -p /workspace/latentsync/latentsync/pipelines/ && "
             "cp /workspace/lipsync_pipeline.py /workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py", "SCRIPTS")

        # 6. Pull Docker + Iniciar container passivo + Patch BasicSR
        print("[AGNO] [6/7] Iniciando container (Docker Pull + Run + Patch)...")
        _ssh(f"sudo docker rm -f lana-engine 2>/dev/null; "
             f"sudo docker pull {DOCKER_IMAGE}; "
             f"sudo docker run -d --name lana-engine --gpus all --network host "
             f"-v /workspace:/workspace -v /mnt/weights:/mnt/weights "
             f"{DOCKER_IMAGE} tail -f /dev/null", "DOCKER")
        
        # Patch BasicSR (compatibilidade torchvision)
        _ssh("sudo docker exec lana-engine bash -c \""
             "sed -i 's/torchvision.transforms.functional_tensor/torchvision.transforms.functional/' "
             "/usr/local/lib/python3.10/dist-packages/basicsr/data/degradations.py 2>/dev/null || true\"", "PATCH")

        # 7. Iniciar Servidor (industrial_main.py)
        print("[AGNO] [7/7] Iniciando Servidor FastAPI...")
        _ssh("sudo docker exec -d lana-engine python3 /workspace/src/industrial_main.py", "SERVER")

        # Health Check
        print("[AGNO] Aguardando servidor responder...")
        for i in range(20):
            time.sleep(5)
            health_res = _ssh("curl -s --connect-timeout 2 http://localhost:8080/health", "HEALTH")
            if "ok" in health_res.stdout:
                print(f"[AGNO] Servidor operacional em {(i+1)*5}s.")
                return
        
        raise Exception("Servidor não respondeu após 100s.")

    def get_ip(self):
        cmd = ["gcloud", "compute", "instances", "describe", self.active_instance, 
               "--project", self.project_id, "--zone", self.active_zone, 
               "--format=\"get(networkInterfaces[0].accessConfigs[0].natIP)\""]
        res = self._run_ssh_cmd(cmd, use_y=False) # Describe não precisa de y
        return res.stdout.strip()

    def heartbeat(self):
        """Envia um pulso de vida para o Sentinela remoto não desligar a máquina."""
        if not self.active_instance: return
        cmd = ["gcloud", "compute", "ssh", self.active_instance, 
               "--project", self.project_id, "--zone", self.active_zone, 
               "--tunnel-through-iap", "--quiet", "--command", 
               "\"touch /workspace/heartbeat\""]
        self._run_ssh_cmd(cmd)

    def _heartbeat_loop(self):
        """Loop infinito de pulso industrial."""
        while True:
            try:
                if self.active_instance:
                    self.heartbeat()
            except: pass
            time.sleep(60)

    def start_heartbeat(self):
        if hasattr(self, 'heartbeat_thread') and self.heartbeat_thread.is_alive():
            return
        import threading
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

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

    def download_result(self, job_id, local_folder=None):
        if local_folder is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_folder = os.path.join(base_dir, "outputs")
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

    def print_triple_progress(self, infra_pc, docker_pc, avatar_pc, infra_msg="", docker_msg="", avatar_msg="", error=False):
        bar_len = 25
        color = "\033[91m" if error else "\033[94m" # Vermelho se erro, azul se normal
        reset = "\033[0m"
        
        def make_bar(pc):
            filled = int(bar_len * (pc / 100))
            return color + "█" * filled + reset + "░" * (bar_len - filled)
            
        sys.stdout.write("\033[F" * 3) # Sobe 3 linhas
        sys.stdout.write(f"\r[INFRA ] |{make_bar(infra_pc)}| {infra_pc}% - {infra_msg}".ljust(110) + "\n")
        sys.stdout.write(f"\r[DOCKER] |{make_bar(docker_pc)}| {docker_pc}% - {docker_msg}".ljust(110) + "\n")
        sys.stdout.write(f"\r[AVATAR] |{make_bar(avatar_pc)}| {avatar_pc}% - {avatar_msg}".ljust(110) + "\n")
        sys.stdout.flush()
        
        # Dashboard JS (Media ponderada para o progresso geral)
        total_p = (infra_pc * 0.2) + (docker_pc * 0.4) + (avatar_pc * 0.4)
        self._update_dashboard_js("PRODUÇÃO TRIPLE", total_p, f"Infra:{infra_msg} | Docker:{docker_msg} | Avatar:{avatar_msg}")

    def _update_dashboard_js(self, step, progress, msg):
        """Exporta o status para o Dashboard visual (JS-Injection)."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(base_dir, "outputs")
        if not os.path.exists(out_dir): os.makedirs(out_dir, exist_ok=True)
        db_path = os.path.join(out_dir, "status_db.js")
        data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "step": step,
            "progress": progress,
            "msg": msg,
            "gpu": self.current_gpu_type,
            "instance": self.active_instance or "Aguardando...",
            "zone": self.active_zone or "Global Search"
        }
        try:
            with open(db_path, "w", encoding="utf-8") as f:
                f.write(f"var LANA_STATUS = {json.dumps(data, indent=2)};")
        except: pass

class AgenteLanaOrchestrator:
    """Orquestrador V16 (Smart Maestro): Resiliência, Autocorreção e Orçamento Inteligente."""
    
    def __init__(self):
        self.engine = LanaIndustrialEngine()

    def generate_audio(self, text, output_path=None):
        if output_path is None:
            import uuid
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_dir = os.path.join(base_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"audio_{uuid.uuid4().hex[:8]}.mp3")
        
        print(f"[TTS] Gerando Sarah (Brazil Identity) para: '{text[:50]}...'")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Preserva sotaque natural
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.80,
                "style": 0.50,
                "use_speaker_boost": True
            }
        }
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200:
            with open(output_path, 'wb') as f: f.write(res.content)
            # Aceleração removida para manter a fidelidade e cadência originais do ElevenLabs
            return output_path
        raise Exception(f"Erro ElevenLabs: {res.text}")

    def criar_avatar_triple(self, audio_path, progress_callback):
        """Cria o avatar com telemetria triple."""
        # 1. Upload do Áudio para o GCS
        progress_callback(30, "Sincronizando áudio com GCS...")
        gcs_path = self.engine.upload_assets(audio_path)
        
        # 2. Criar Job via MCP
        progress_callback(40, "Injetando Job via MCP Bridge...")
        job_res = self.engine.call_mcp_tool("create_render_job", {
            "audio_url": gcs_path,
            "presenter_id": "default"
        })
        
        if not job_res or "error" in job_res:
            raise Exception(f"Falha ao criar job MCP: {job_res}")
            
        job_id = job_res.get("id") or job_res.get("job_id")
        
        # 3. Polling via MCP
        progress_callback(50, "Iniciando Renderização GPU...")
        last_progress = 50
        stuck_count = 0
        
        for i in range(120): # 20 minutos max
            time.sleep(15) # Aumentado intervalo para reduzir ruído de polling
            status_res = self.engine.call_mcp_tool("get_render_status", {"job_id": job_id})
            
            if not status_res or "error" in status_res:
                print(f"\n[CRITICAL] Falha detectada no motor remoto: {status_res.get('error') if status_res else 'Vazio'}")
                raise Exception(f"Erro no Motor de Vegas: {status_res}")
                
            status = status_res.get("status")
            
            if status == "completed":
                progress_callback(90, "Render Concluído! Baixando...")
                return self.engine.download_result(job_id)
            elif status in ("failed", "error"):
                error_msg = status_res.get("error", "Erro desconhecido na GPU")
                print(f"\n[CRITICAL] JOB FALHOU EM VEGAS: {error_msg}")
                raise Exception(f"Job Failed: {error_msg}")
                
            # Detecção de Travamento (Stuck Detection)
            # Se o status não mudar em 5 minutos (20 iterações), algo está errado
            current_p = 50 + (i * 0.3) # Simulação visual de progresso se o motor não enviar % exata
            progress_callback(min(89, int(current_p)), f"Renderizando em Vegas (Job: {job_id[:8]})")
            
            # Autocorreção: Se o motor sumiu da lista de processos (nvidia-smi check indireto via status)
            if status == "not_found":
                raise Exception("Job desapareceu do servidor. Possível reinicialização do container.")
            
            # Fim do Loop de Polling
        
        raise Exception("Timeout na renderização do vídeo (20min+)")
    def produce_video_from_text(self, text, index=1, total=1, force_gpu="ALL"):
        """Pipeline visual industrial com detecção de erro em tempo real."""
        # Estado inicial das barras
        infra_pc, docker_pc, avatar_pc = 0, 0, 0
        infra_msg, docker_msg, avatar_msg = "Aguardando...", "Aguardando...", "Aguardando..."
        
        def update_view(i_pc=None, d_pc=None, a_pc=None, i_m=None, d_m=None, a_m=None, err=False):
            nonlocal infra_pc, docker_pc, avatar_pc, infra_msg, docker_msg, avatar_msg
            if i_pc is not None: infra_pc = i_pc
            if d_pc is not None: docker_pc = d_pc
            if a_pc is not None: avatar_pc = a_pc
            if i_m: infra_msg = i_m
            if d_m: docker_msg = d_m
            if a_m: avatar_msg = a_m
            self.engine.print_triple_progress(infra_pc, docker_pc, avatar_pc, infra_msg, docker_msg, avatar_msg, error=err)

        print("\n" * 3) # Espaço para as 3 barras
        try:
            # 1. Preparar Infra
            update_view(i_pc=5, i_m="Iniciando...")
            ip = self.engine.ensure_instance_ready(progress_callback=lambda m: update_view(i_m=m), force_gpu=force_gpu)
            update_view(i_pc=100, i_m="Ativa")
            
            # 2. Preparar Docker/Scripts
            update_view(d_pc=50, d_m="Sincronizando Scripts...")
            # O bootstrap_v18 já é chamado dentro de ensure_instance_ready
            update_view(d_pc=100, d_m="Pronto")
            
            # 3. Gerar Áudio (TTS)
            update_view(a_pc=10, a_m="Gerando Voz Sarah...")
            audio_path = self.generate_audio(text)
            update_view(a_pc=40, a_m="Áudio Sincronizado")
            
            # 4. Renderizar Vídeo
            video_path = self.criar_avatar_triple(audio_path, progress_callback=lambda pc, m: update_view(a_pc=pc, a_m=m))
            update_view(a_pc=100, a_m="Sucesso!")
            
            return {"status": "success", "video_path": video_path}
            
        except Exception as e:
            error_msg = str(e)[:100]
            # Pintar as barras de VERMELHO e parar
            update_view(err=True, a_m=f"FALHA: {error_msg}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    maestro = AgenteLanaOrchestrator()
    maestro.produce_video_from_text("O pipeline V17 Zero Crash está agora operacional. Blindagem de memória e orquestração inteligente ativadas.")
