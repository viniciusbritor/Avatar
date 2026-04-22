import os
import subprocess
import uuid
import time
import json
import sys
import logging

# Configuração de Logs para stderr (stdout é reservado para o MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

class LanaMCPServer:
    """Servidor MCP Industrial para controle do Motor Lana via Stdio."""
    
    def __init__(self):
        self.jobs = {}
        self.workspace = "/workspace"
        self.image_name = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0"

    def handle_request(self, request):
        try:
            method = request.get("method")
            params = request.get("params", {})
            id_ = request.get("id")

            if method == "create_render_job":
                result = self.create_render_job(params.get("audio_url"), params.get("presenter_id"))
            elif method == "get_render_status":
                result = self.get_render_status(params.get("job_id"))
            elif method == "cleanup":
                result = self.cleanup()
            else:
                result = {"error": "Method not found"}

            return {"jsonrpc": "2.0", "result": result, "id": id_}
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            return {"jsonrpc": "2.0", "error": str(e), "id": request.get("id")}

    def create_render_job(self, audio_url, presenter_id):
        job_id = str(uuid.uuid4())
        logging.info(f"Iniciando Job: {job_id} para {presenter_id}")
        
        # Como o MCP é stdio e não queremos bloquear, 
        # o 'industrial_main.py' ainda é útil como worker dentro do Docker, 
        # mas aqui o MCP é o orquestrador do container.
        
        # Na verdade, para ser 100% resiliente, vamos apenas disparar o job 
        # enviando para o container que já deve estar rodando.
        try:
            # Tentar enviar para a API local (localhost dentro da VM)
            import requests
            payload = {
                "presenter_id": presenter_id,
                "script": {"type": "audio", "audio_url": audio_url}
            }
            res = requests.post("http://localhost:8080/clips", json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                data["mcp_job_id"] = job_id
                return data
            return {"error": f"Internal API failed: {res.text}"}
        except Exception as e:
            return {"error": f"Connection to container failed: {str(e)}"}

    def get_render_status(self, job_id):
        try:
            import requests
            res = requests.get(f"http://localhost:8080/clips/{job_id}", timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"error": "Job not found in container"}
        except Exception as e:
            return {"error": str(e)}

    def cleanup(self):
        logging.info("Executando limpeza industrial...")
        subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)
        return {"status": "cleaned"}

    def run(self):
        logging.info("Lana MCP Server Started (Stdio Mode)")
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                logging.error(f"Invalid JSON: {line}")

if __name__ == "__main__":
    server = LanaMCPServer()
    server.run()
