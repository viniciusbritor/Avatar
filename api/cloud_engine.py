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
    Versão do Engine compatível com Cloud Run.
    Herda 100% do original. Sobrescreve apenas _create_gpu_instance
    para usar o caminho do startup script via variável de ambiente.
    """

    def _create_gpu_instance(self, name, zone):
        """
        Cria uma instância L4. Idêntico ao original, mas o caminho do
        startup script é resolvido via env var STARTUP_SCRIPT_PATH.
        """
        startup_script_path = os.getenv(
            "STARTUP_SCRIPT_PATH",
            "/app/infra/startup_arch4.sh"  # Padrão dentro do container Docker
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

        res = subprocess.run(" ".join(cmd), capture_output=True, text=True, shell=True)
        if res.returncode != 0:
            print(f"[ERROR] Falha ao criar instância em {zone}: {res.stderr}")
            return False, res.stderr
        return True, ""
