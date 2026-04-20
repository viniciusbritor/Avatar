import requests
import time
import os

API_URL = "http://35.245.195.107:8080"

JOBS = [
    {"id": "tse_intro_hd", "audio": "/app/assets/cris_intro_tse.mp3", "presenter": "lana_intro"},
    {"id": "tse_outro_hd", "audio": "/app/assets/cris_outro_tse.mp3", "presenter": "lana_outro"}
]

def trigger_job(job_config):
    print(f"--- Disparando Job: {job_config['id']} ---")
    payload = {
        "script": {"text": "TSE Production"}, # Espera um dicionario
        "audio_path": job_config["audio"],
        "presenter_id": job_config["presenter"],
        "resolution": 512
    }
    try:
        response = requests.post(f"{API_URL}/clips", json=payload, timeout=30)
        if response.status_code in [200, 201]:
            return response.json()["id"]
        else:
            print(f"FAILED: Erro ao disparar {job_config['id']}: {response.text}")
            return None
    except Exception as e:
        print(f"FAILED: Erro de conexao: {str(e)}")
        return None

def poll_job(job_id):
    print(f"Monitorando renderizacao do Job: {job_id}")
    while True:
        try:
            response = requests.get(f"{API_URL}/clips/{job_id}", timeout=10)
            if response.status_code == 200:
                status = response.json()["status"]
                if status == "done" or status == "completed":
                    print(f"SUCCESS: Video pronto: {response.json()['result_url']}")
                    return response.json()['result_url']
                elif status == "error":
                    print(f"FAILED: Erro no Job: {response.json().get('error')}")
                    return None
            else:
                print(f"WARNING: Erro ao checar status: {response.status_code}")
        except Exception as e:
            print(f"WARNING: Alerta de conexao: {str(e)}")
        
        time.sleep(30)
        print(".", end="", flush=True)

if __name__ == "__main__":
    results = []
    for job in JOBS:
        real_id = trigger_job(job)
        if real_id:
            url = poll_job(real_id)
            if url:
                results.append(url)
    
    print("\n--- PRODUCAO CONCLUIDA ---")
    for r in results:
        print(f"MP4: {r}")
