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
from agno.models.google import Gemini
from google.cloud import storage
from src.secrets_manager import get_secret

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
            
        import sys
        if sys.platform != "win32":
            use_y = False
            
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

    def _find_existing_engines(self):
        """Busca por instâncias industriais já em execução usando a API nativa do GCP."""
        print("[MAESTRO] Buscando motores ativos via API Nativa...")
        try:
            from google.cloud import compute_v1
            client = compute_v1.InstancesClient()
            
            # Busca em todas as zonas do projeto (Aggregated List)
            request = compute_v1.AggregatedListInstancesRequest(project=self.project_id)
            agg_list = client.aggregated_list(request=request)
            
            instances = []
            for zone, response in agg_list:
                if response.instances:
                    for inst in response.instances:
                        # Filtro: Nome começa com lana-engine- e está RUNNING
                        if inst.name.startswith("lana-engine-") and inst.status == "RUNNING":
                            instances.append({
                                "name": inst.name,
                                "zone": zone.split('/')[-1]
                            })
            
            if instances:
                # Retorna ordenado do mais novo pro mais antigo
                inst_sorted = sorted(instances, key=lambda x: x['name'], reverse=True)
                print(f"[REUSE] Motores detectados via API: {len(inst_sorted)}")
                return inst_sorted
            else:
                print("[MAESTRO] Nenhum motor ativo encontrado nas zonas do projeto.")
                
        except Exception as e:
            print(f"[ERROR] Falha na detecção nativa de instâncias: {e}")
            
        return []

    def ensure_instance_ready(self, progress_callback=None, force_gpu="ALL"):
        """Garante uma máquina pronta, utilizando exclusivamente NVIDIA L4 e roteamento inteligente (Auto-Scale)."""
        import uuid
        import requests
        
        # 1. Tentar REUSO (Procurar máquinas ociosas)
        existing_instances = self._find_existing_engines()
        for inst in existing_instances:
            existing_name = inst['name']
            existing_zone = inst['zone']
            
            self.active_instance = existing_name
            self.active_zone = existing_zone
            
            if self._test_ssh(existing_name, existing_zone, max_retries=2, progress_callback=progress_callback):
                self._ensure_server_running() # Garante que o /health está acessível
                ip = self.get_ip()
                if ip:
                    try:
                        # Roteamento Inteligente: Testa o estado de Lock da GPU
                        res = requests.get(f"http://{ip}:8080/health", timeout=3)
                        health_data = res.json()
                        if not health_data.get("busy", False):
                            if progress_callback: progress_callback("Reusando motor L4 livre.")
                            self.start_heartbeat()
                            return ip
                        else:
                            print(f"[SCALE-OUT] Máquina {existing_name} Ocupada. Passando para a próxima...")
                    except Exception as e:
                        print(f"[WARN] Healthcheck falhou em {existing_name}, assumindo ocupada/quebrada.")
            
            # Se chegou aqui, ou ssh falhou ou a máquina está ocupada.
            # Limpeza apenas se for uma máquina zumbi inalcançável (opcional). 
            # O ideal é não purgar se estiver apenas ocupada, pois o Sentinel lidará com ela.
            self.active_instance = None
            self.active_zone = None

        # 2. ESCALA HORIZONTAL: Criar nova L4 (Nenhuma livre encontrada)
        print("[MAESTRO] Nenhuma L4 livre. Acionando Scale-Out (NVIDIA L4)...")
        for zone in self.l4_zones:
            # Nome único por milissegundo + UUID para evitar colisão absoluta entre 5 requisições simultâneas
            new_name = f"lana-engine-l4-{int(time.time())}-{uuid.uuid4().hex[:4]}"
            if progress_callback: progress_callback(f"Scale-Out Spawn em {zone}...")
            
            for attempt in range(2):
                success, error_msg = self._create_gpu_instance(new_name, zone)
                if success:
                    if self._test_ssh(new_name, zone, max_retries=15, progress_callback=progress_callback):
                        self.active_instance = new_name
                        self.active_zone = zone
                        self.current_gpu_type = "L4"
                        self.start_heartbeat()
                        # IMPORTANTE: Como a imagem atual (deeplearning-platform-release) não tem nada salvo, 
                        # DEIXE False para baixar tudo. Quando criar a sua Custom Gold Image, mude para True!
                        self.bootstrap_v18(is_prebaked=False)
                        return self.get_ip()
                    self._purge_zone(new_name, zone)
                    break # Pula para a próxima zona se o SSH falhou
                
                if "Quota" in error_msg or "GPUS_ALL_REGIONS" in error_msg:
                    print(f"[QUOTA] Cota de GPU cheia na zona. Aguardando 60s (Tentativa {attempt+1}/2)...")
                    time.sleep(60)
                    continue
                else:
                    break # Stockout, pula para próxima zona

        raise Exception("CATÁSTROFE: Limite máximo Global de GPUs atingido ou cotas estouradas!")

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
        """Faz a chamada HTTP direta para o IP da instância, sem túnel SSH frágil."""
        ip = self.get_ip()
        if not ip:
            return {"error": "Não foi possível obter o IP da máquina para conexão."}
        
        import requests
        # Mapeamento de métodos MCP para Endpoints HTTP
        if method == "create_render_job":
            url = f"http://{ip}:8080/clips"
            payload = {
                "presenter_id": params.get("presenter_id", "default"),
                "script": {
                    "type": "audio",
                    "audio_url": params.get("audio_url")
                }
            }
            try:
                res = requests.post(url, json=payload, timeout=15)
                return res.json()
            except Exception as e:
                return {"error": f"Falha HTTP POST: {str(e)}"}
                
        elif method == "get_render_status":
            job_id = params.get("job_id")
            url = f"http://{ip}:8080/clips/{job_id}"
            try:
                res = requests.get(url, timeout=10)
                return res.json()
            except Exception as e:
                return {"error": f"Falha HTTP GET: {str(e)}"}
        else:
            return {"error": f"Método {method} não suportado via HTTP."}

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
            "\"curl -s --connect-timeout 2 http://localhost:8080/health > /dev/null && echo 'SERVER_OK'\"",
            "--quiet"
        ]
        health_res = self._run_ssh_cmd(health_cmd)
        if "SERVER_OK" in health_res.stdout:
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
        """
        Bootstrap Cirúrgico e Limpo (Serverless-like).
        Assume que a imagem Docker (avatar-l4) já contém as dependências pesadas (LatentSync, FastAPI, etc).
        Apenas sincroniza scripts/assets rápidos do bucket e sobe a API.
        """
        GCS_SCRIPTS = "gs://brasil-ai-avatars-vault/scripts"
        DOCKER_IMAGE = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.8"
        
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

        print("\n[AGNO] === INICIANDO BOOTSTRAP LIMPO (V3) ===")
        
        # 1. Preparar filesystem e autenticação
        print("[AGNO] [1/5] Preparando ambiente...")
        for _ in range(3):
            res = _ssh("sudo mkdir -p /workspace/src /workspace/outputs/temp /workspace/latentsync/assets && "
                       "sudo chmod -R 777 /workspace && "
                       "sudo gcloud auth configure-docker us-east1-docker.pkg.dev --quiet", "PREP")
            if res.returncode == 0: break
            time.sleep(5)
        else:
            raise Exception(f"Falha no setup inicial: {res.stderr}")

        # 2. Sincronizar Assets e Scripts do Bucket (Rápido, 100% Nuvem)
        print("[AGNO] [2/5] Sincronizando Assets e Scripts (Bucket)...")
        _ssh(f"gsutil -m cp gs://lana-weights-universal/assets/*.mp4 /workspace/latentsync/assets/ 2>/dev/null || true && "
             f"gsutil -m cp {GCS_SCRIPTS}/* /workspace/ 2>/dev/null || true", "BUCKET_SYNC")

        # 3. Preparar Golden Disk (Modelos grandes montados instantaneamente)
        print("[AGNO] [3/5] Mapeando Discos de Modelos...")
        _ssh("rm -rf /workspace/latentsync/checkpoints && "
             "ln -sfn /mnt/weights /workspace/latentsync/checkpoints 2>/dev/null || true", "CHECKPOINTS")

        # 4. Pull e Run do Docker (Imagem Imutável)
        print("[AGNO] [4/5] Iniciando Motor de IA (Docker)...")
        api_key = get_secret("API_SECRET_KEY", fallback="brasilai-avatar-2026")
        
        pull_cmd = f"sudo docker pull {DOCKER_IMAGE}; " if not is_prebaked else ""
        
        _ssh(f"sudo docker rm -f lana-engine 2>/dev/null; "
             f"{pull_cmd}"
             f"sudo docker run -d --name lana-engine --gpus all --network host "
             f"-e API_SECRET_KEY='{api_key}' "
             f"-v /workspace:/workspace -v /mnt/weights:/mnt/weights "
             f"{DOCKER_IMAGE} tail -f /dev/null", "DOCKER")

        # 5. Ligar a API RESTful
        print("[AGNO] [5/5] Subindo API RESTful...")
        # Fallback tolerante para pacotes básicos caso a v2.8 ainda não os tenha.
        _ssh("sudo docker exec -d lana-engine bash -c \"pip install fastapi uvicorn google-cloud-storage requests python-multipart >/dev/null 2>&1 || true; python3 /workspace/industrial_main.py > /workspace/outputs/temp/server.log 2>&1\"", "SERVER")

        # Health Check
        print("[AGNO] Aguardando servidor responder (REST API)...")
        for i in range(24): # 120 segundos total
            time.sleep(5)
            health_res = _ssh("curl -s --connect-timeout 2 http://localhost:8080/health > /dev/null && echo 'SERVER_OK'", "HEALTH")
            if "SERVER_OK" in health_res.stdout:
                print(f"[AGNO] API operacional em {(i+1)*5}s. Máquina Pronta!")
                return
        
        raise Exception("API não respondeu após 120s. Verifique os logs do Docker.")

    def get_ip(self):
        """Recupera o IP público da máquina usando SDK Nativo, sem bash."""
        try:
            from google.cloud import compute_v1
            client = compute_v1.InstancesClient(project=self.project_id)
            instance = client.get(project=self.project_id, zone=self.active_zone, instance=self.active_instance)
            # Retorna o IP NAT externo
            return instance.network_interfaces[0].access_configs[0].nat_i_p
        except Exception as e:
            print(f"[SDK] Erro ao recuperar IP nativo: {e}")
            return None

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

    def upload_assets(self, local_path, job_id=None):
        """Upload de assets para o GCS usando SDK nativo."""
        filename = os.path.basename(local_path)
        gcs_path = f"gs://{self.bucket_name}/temp/{filename}"
        jid_log = f"[JOB {job_id[:8]}] " if job_id else ""
        print(f"{jid_log}[GCS] Sincronizando: {gcs_path}")
        
        try:
            from google.cloud import storage
            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(f"temp/{filename}")
            blob.upload_from_filename(local_path)
            self.heartbeat() # Atividade detectada
            return gcs_path
        except Exception as e:
            print(f"{jid_log}[ERROR] Falha no upload GCS: {e}")
            raise e

    def download_result(self, job_id, local_folder=None):
        """Download do resultado final usando SDK nativo."""
        if local_folder is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_folder = os.path.join(base_dir, "outputs")
        
        now = datetime.now()
        timestamp = now.strftime("%d_%m_%Y_%H_%M_%S")
        filename = f"lana_{timestamp}_{job_id}.mp4"
        gcs_blob_name = f"outputs/final_{job_id}.mp4"
        local_path = os.path.abspath(os.path.join(local_folder, filename))
        
        if not os.path.exists(local_folder): os.makedirs(local_folder)
        print(f"[JOB {job_id[:8]}] [GCS] Download Final: {gcs_blob_name} -> {filename}")
        
        try:
            from google.cloud import storage
            client = storage.Client(project=self.project_id)
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_blob_name)
            blob.download_to_filename(local_path)
            self.heartbeat() # Pulso final de entrega
            print(f"[JOB {job_id[:8]}] [SUCCESS] Video entregue: {local_path}")
            return local_path
        except Exception as e:
            print(f"[JOB {job_id[:8]}] [ERROR] Falha no download final: {e}")
            raise e

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
    """Orquestrador V18 (Cognitive Maestro): Resiliência e Autocorreção via Agno Agent."""
    
    def __init__(self):
        self.engine = LanaIndustrialEngine()
        
        gemini_key = get_secret("GEMINI_API_KEY")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["GOOGLE_API_KEY"] = gemini_key
            
        self.infra_pc, self.docker_pc, self.avatar_pc = 0, 0, 0
        self.infra_msg, self.docker_msg, self.avatar_msg = "Aguardando...", "Aguardando...", "Aguardando..."

        # Inicializa o Cérebro Cognitivo
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-flash"),
            description="Você é o Maestro Industrial, o orquestrador autônomo da produção de Avatares da Brasil AI.",
            instructions=[
                "Seu objetivo é iniciar a produção de um vídeo de avatar dado um texto e um ID de trabalho.",
                "Siga EXATAMENTE esta ordem linear de ferramentas:",
                "1. Chame `prepare_gpu_infrastructure` para garantir que o motor na nuvem está ativo.",
                "2. Chame `generate_and_upload_audio` com o texto para criar a voz e o GCS path.",
                "3. Chame `dispatch_render_job` passando o GCS path do áudio, o job_id e o webhook_url, para delegar a renderização assíncrona à GPU.",
                "Se alguma ferramenta retornar uma string com 'ERRO', você DEVE analisar o motivo e tentar contornar ou repetir a chamada (máximo 2 vezes).",
                "Sua resposta final ao usuário DEVE incluir a palavra 'SUCESSO' confirmando que o job foi despachado para a GPU com sucesso."
            ],
            tools=[self.prepare_gpu_infrastructure, self.generate_and_upload_audio, self.dispatch_render_job],
            markdown=True
        )

    def _update_view(self, i_pc=None, d_pc=None, a_pc=None, i_m=None, d_m=None, a_m=None, err=False):
        if i_pc is not None: self.infra_pc = i_pc
        if d_pc is not None: self.docker_pc = d_pc
        if a_pc is not None: self.avatar_pc = a_pc
        if i_m: self.infra_msg = i_m
        if d_m: self.docker_msg = d_m
        if a_m: self.avatar_msg = a_m
        self.engine.print_triple_progress(self.infra_pc, self.docker_pc, self.avatar_pc, self.infra_msg, self.docker_msg, self.avatar_msg, error=err)

    def generate_audio_local(self, text, output_path=None):
        """TTS Nativo. Chamado apenas pela ferramenta do Agente."""
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
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.50, "similarity_boost": 0.80, "style": 0.50, "use_speaker_boost": True}
        }
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200:
            with open(output_path, 'wb') as f: f.write(res.content)
            return output_path
        raise Exception(f"Erro ElevenLabs: {res.text}")

    # --- AGNO TOOLS ---

    def prepare_gpu_infrastructure(self) -> str:
        """Garante que a máquina GPU L4 na nuvem está provisionada e pronta. Retorna uma mensagem de sucesso com IP ou erro."""
        self._update_view(i_pc=5, i_m="Acionando Agente Infra...")
        try:
            ip = self.engine.ensure_instance_ready(progress_callback=lambda m: self._update_view(i_m=m))
            self._update_view(i_pc=100, i_m="GPU L4 Ativa", d_pc=100, d_m="Container Pronto")
            return f"Sucesso. GPU Pronta. IP Operacional: {ip}"
        except Exception as e:
            self._update_view(err=True, i_m=f"FALHA GPU: {str(e)[:50]}")
            return f"ERRO ao preparar GPU: {str(e)}"

    def generate_and_upload_audio(self, text: str, job_id: str) -> str:
        """Gera a voz em TTS a partir do texto e envia para o Cloud Storage. Retorna o GCS Path (gs://...)."""
        self._update_view(a_pc=10, a_m="Gerando Voz Sarah (Cognitivo)...")
        try:
            local_audio = self.generate_audio_local(text)
            self._update_view(a_pc=30, a_m="Sincronizando áudio GCS...")
            gcs_path = self.engine.upload_assets(local_audio, job_id=job_id)
            self._update_view(a_pc=40, a_m="Áudio no GCS")
            return gcs_path
        except Exception as e:
            self._update_view(err=True, a_m=f"FALHA Áudio: {str(e)[:50]}")
            return f"ERRO no TTS/Upload: {str(e)}"

    def dispatch_render_job(self, audio_gcs_url: str, job_id: str, webhook_url: str = None) -> str:
        """Envia o comando de renderização assíncrono para a GPU via MCP."""
        self._update_view(a_pc=45, a_m="Injetando Job via MCP (Cognitivo)...")
        try:
            job_res = self.engine.call_mcp_tool("create_render_job", {
                "audio_url": audio_gcs_url,
                "presenter_id": "default",
                "webhook_url": webhook_url,
                "job_id": job_id
            })
            if not job_res or "error" in job_res:
                return f"ERRO ao despachar job: {job_res}"
            self._update_view(a_pc=100, a_m="Renderização Assíncrona Delegada à GPU!")
            return f"Sucesso! Job delegado para processamento em background (Async). ID Remoto: {job_id}"
        except Exception as e:
            return f"ERRO ao despachar job: {str(e)}"

    def wait_and_download_video(self, job_id: str) -> str:
        """Faz polling na GPU até a conclusão do vídeo e o baixa localmente. Retorna o caminho absoluto do vídeo."""
        try:
            for i in range(120): # 30 minutos max (15s * 120)
                time.sleep(15)
                status_res = self.engine.call_mcp_tool("get_render_status", {"job_id": job_id})
                if not status_res or "error" in status_res:
                     return f"ERRO crítico no motor: {status_res}"
                status = status_res.get("status")
                
                current_p = min(89, 50 + (i * 0.3))
                self._update_view(a_pc=int(current_p), a_m=f"Renderizando Autônomo ({status})...")
                
                if status == "completed":
                    self._update_view(a_pc=90, a_m="Baixando Vídeo...")
                    local_path = self.engine.download_result(job_id)
                    self._update_view(a_pc=100, a_m="Sucesso Absoluto!")
                    return f"Sucesso! Vídeo final baixado em: {local_path}"
                elif status in ("failed", "error"):
                    return f"ERRO: Renderização falhou na GPU: {status_res.get('error')}"
                elif status == "not_found":
                    return "ERRO: Job desapareceu da GPU (crash de memória?)."
            return "ERRO: Timeout após 30 minutos aguardando GPU."
        except Exception as e:
            return f"ERRO no polling: {str(e)}"

    # --- ENTRADA DO PIPELINE ---

    def produce_video_from_text(self, text: str, job_id=None, index=1, total=1, force_gpu="ALL", webhook_url=None):
        """Pipeline visual acionado pelo Cérebro Agno."""
        if job_id is None:
            import uuid
            job_id = uuid.uuid4().hex[:8]
            
        print(f"\n[JOB {job_id[:8]}] >>> INICIANDO PRODUÇÃO COGNITIVA (AGNO) <<<")
        print("\n" * 3) # Espaço para as 3 barras
        
        # Reset visual
        self._update_view(0, 0, 0, "Aguardando Orquestrador...", "Aguardando...", "Aguardando...")
        
        try:
            prompt = f"Produza um vídeo para o texto '{text}'. O Job ID é '{job_id}'. "
            if webhook_url:
                prompt += f"Passe o webhook_url '{webhook_url}' para o dispatch_render_job."
                
            run_response = self.agent.run(prompt)
            resposta = run_response.content
            
            print(f"\n[AGNO MAESTRO] Relatório de Missão:\n{resposta}")
            
            if "SUCESSO" in resposta.upper():
                return {"status": "success", "video_path": "Assíncrono (Será via Webhook)"}
            else:
                self._update_view(err=True, a_m="Agente abortou por falha irrecuperável.")
                return {"status": "error", "message": resposta}
                
        except Exception as e:
            error_msg = str(e)[:100]
            self._update_view(err=True, a_m=f"FALHA FATAL DO AGENTE: {error_msg}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    maestro = AgenteLanaOrchestrator()
    maestro.produce_video_from_text("Testando a Orquestração Cognitiva Agno. O Agente agora tem total controle do fluxo e ferramentas.")
