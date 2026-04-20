import requests
import time

API_URL = "http://35.245.195.107:8080"

def run_launch_demo():
    print("=== LANÇAMENTO BRASIL EIAI: LANA HD ===")
    
    payload = {
        "presenter_id": "lana_comentario",
        "script": {
            "type": "audio",
            "audio_url": "local_path_used" # Ignorado pelo parser novo se audio_path estiver presente
        },
        "audio_path": "/app/assets/cris_fala_lancamento.mp3", # NOVO PARÂMETRO
        "resolution": 512
    }
    
    try:
        print(f"1. Enviando pedido de lançamento para o Motor...")
        response = requests.post(f"{API_URL}/clips", json=payload, timeout=60)
        
        if response.status_code == 200:
            job_id = response.json().get("id")
            print(f"DONE: Job criado! ID: {job_id}")
            
            # Polling para verificar status
            print(f"2. Monitorando renderizacao (Ultra-HD)...")
            while True:
                status_res = requests.get(f"{API_URL}/clips/{job_id}")
                if status_res.status_code == 200:
                    data = status_res.json()
                    status = data.get("status")
                    print(f"   - Status: {status}")
                    
                    if status == "done":
                        print(f"\nSUCCESS: VIDEO CONCLUIDO!")
                        print(f"URL: {data.get('result_url')}")
                        break
                    elif status == "error":
                        print(f"FAILED: Erro no processamento: {data.get('error')}")
                        break
                
                time.sleep(10)
        else:
            print(f"FAILED: Erro ao criar Job: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"FAILED: Erro na conexao: {str(e)}")

if __name__ == "__main__":
    run_launch_demo()
