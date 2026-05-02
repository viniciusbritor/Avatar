"""
cloud_engine.py — Brasil AI Avatar API (Cloud Run Edition)
------------------------------------------------------------
Subclasse do LanaIndustrialEngine que sobrescreve APENAS o que é
necessário para rodar dentro do Cloud Run (Linux, gcloud instalado
via Dockerfile). O código original em src/ não é tocado.

Diferenças em relação ao engine local (Windows):
  - startup_script_path: lido via env var STARTUP_SCRIPT_PATH
    (padrão: /app/infra/startup_arch4.sh, dentro do container)
  - Sem dependências de caminhos Windows (c:/Users/vinic/...)
"""

import os
import sys
import subprocess

# Adiciona src/ ao path sem modificar o código original
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agente_lana_orchestrator import LanaIndustrialEngine, L4_MACHINE


class CloudLanaEngine(LanaIndustrialEngine):
    """
    Versão do Engine compatível com Cloud Run (Linux).
    Sobrescreve:
      - _create_gpu_instance: usa env var para o startup script path
      - _run_ssh_cmd: remove 'echo y |' Windows, usa stdin=DEVNULL
    """

    def _create_gpu_instance(self, name, zone):
        """Cria instância L4 com startup script do container."""
        startup_script_path = os.getenv(
            "STARTUP_SCRIPT_PATH",
            "/app/infra/startup_arch4.sh"
        )
        if not os.path.exists(startup_script_path):
            return False, f"Startup script não encontrado: {startup_script_path}"

        cmd = [
            "gcloud", "compute", "instances", "create", name,
            "--project", self.project_id, "--zone", zone,
            f"--machine-type={L4_MACHINE}",
            "--image-family=common-cu129-ubuntu-2204-nvidia-580",
            "--image-project=deeplearning-platform-release",
            "--accelerator=type=nvidia-l4,count=1",
            "--boot-disk-size=150GB",
            "--provisioning-model=STANDARD",
            "--maintenance-policy=TERMINATE",
            f"--metadata-from-file=startup-script={startup_script_path}",
            "--scopes=cloud-platform",
            "--quiet"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if res.returncode != 0:
            print(f"[ERROR] Falha ao criar instância em {zone}: {res.stderr}")
            return False, res.stderr
        return True, ""

    def _test_ssh(self, name, zone, max_retries=15, progress_callback=None):
        """
        Override para Linux: remove as aspas escapadas do --command
        que no Windows usavam shell=True mas no Linux causam
        'bash: command not found' porque as aspas viram parte do comando.
        """
        import time
        for i in range(max_retries):
            if progress_callback:
                progress_callback(f"Teste SSH ({i+1}/{max_retries})...")
            cmd = [
                "gcloud", "compute", "ssh", name,
                "--project", self.project_id,
                "--zone", zone,
                "--tunnel-through-iap",
                "--command", "echo SSH_OK",   # Sem aspas escapadas
                "--quiet",
                "--ssh-flag=-o StrictHostKeyChecking=no",
                "--ssh-flag=-o UserKnownHostsFile=/dev/null",
                "--ssh-flag=-o LogLevel=ERROR"
            ]
            res = self._run_ssh_cmd(cmd)
            if res.returncode == 0 and "SSH_OK" in res.stdout:
                print(f"[MAESTRO] SSH estabelecido com {name}.")
                return True
            else:
                print(f"[DEBUG] SSH Fail ({i+1}/{max_retries}): code={res.returncode}, err='{res.stderr.strip()[:100]}'")
            time.sleep(10)
        print(f"[ERROR] Falha de SSH com {name} após {max_retries} tentativas.")
        return False

    def _find_existing_engine(self):
        """Override: usa lista nativa (sem shell=True, sem 2>NUL Windows)."""
        print("[MAESTRO] Buscando motores ativos no GCP...")
        cmd = [
            "gcloud", "compute", "instances", "list",
            f"--filter=name~lana-engine- AND status=RUNNING",
            "--format=json",
            "--project", self.project_id,
            "--quiet"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, encoding="utf-8", errors="ignore")
        if res.returncode == 0 and res.stdout.strip():
            try:
                import json
                instances = json.loads(res.stdout)
                if instances:
                    inst = sorted(instances, key=lambda x: x['name'], reverse=True)[0]
                    print(f"[REUSE] Motor detectado: {inst['name']}")
                    return inst['name'], inst['zone'].split('/')[-1]
            except Exception:
                pass
        return None, None

    def _purge_zone(self, name, zone):
        """Override: sem shell=True nem 2>NUL (Windows-only). Compatível com Linux."""
        print(f"[ZERO-WASTE] Purgando {name} em {zone}...")
        subprocess.run(
            ["gcloud", "compute", "instances", "delete", name,
             "--project", self.project_id, "--zone", zone,
             "--delete-disks=all", "--quiet"],
            capture_output=True, stdin=subprocess.DEVNULL
        )
        subprocess.run(
            ["gcloud", "compute", "disks", "delete", name,
             "--project", self.project_id, "--zone", zone, "--quiet"],
            capture_output=True, stdin=subprocess.DEVNULL
        )

    def _run_ssh_cmd(self, cmd_list, use_y=True, capture=True):
        """
        Override para Cloud Run (Linux).
        Remove o 'echo y |' do Windows. Usa stdin=DEVNULL + --quiet
        + StrictHostKeyChecking=no para evitar qualquer prompt interativo.
        """
        if isinstance(cmd_list, list):
            cmd = list(cmd_list)
            if "--quiet" not in cmd:
                cmd.append("--quiet")
            cmd_str = " ".join(cmd)
            if "compute ssh" in cmd_str and "--ssh-flag" not in cmd_str:
                cmd += [
                    "--ssh-flag=-o StrictHostKeyChecking=no",
                    "--ssh-flag=-o UserKnownHostsFile=/dev/null",
                    "--ssh-flag=-o LogLevel=ERROR"
                ]
        else:
            cmd = cmd_list

        res = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            stdin=subprocess.DEVNULL,
            encoding="utf-8",
            errors="ignore"
        )
        return res

    def get_ip(self):
        """Override: usa gcloud CLI para obter IP externo (sem compute_v1)."""
        import json
        cmd = [
            "gcloud", "compute", "instances", "describe",
            self.active_instance,
            "--project", self.project_id,
            "--zone", self.active_zone,
            "--format=json(networkInterfaces[0].accessConfigs[0].natIP)",
            "--quiet"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True,
                             stdin=subprocess.DEVNULL, encoding="utf-8", errors="ignore")
        if res.returncode == 0 and res.stdout.strip():
            try:
                data = json.loads(res.stdout)
                return data["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
            except Exception:
                pass
        return None
