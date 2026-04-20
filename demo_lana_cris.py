import requests
import time
import os
import sys

# Cores para o terminal
GREEN = "\033[92m"
BLUE = "\033[94m"
END = "\033[0m"

def run_cris_demo():
    # IP da nossa VM GCE (Fixo conforme provisionado)
    API_URL = "http://8.228.74.200:8080"
    LOCAL_OUTPUT_DIR = "demo_results"
    os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
    
    print(f"{BLUE}=== LANA AVATAR DEMO: CRIS (BRASIL AI) ==={END}")
    
    # 1. Preparar o áudio local (Cris fala gerada anteriormente)
    # Em produção, a API baixaria de uma URL pública. Para a demo, 
    # vpu simular que o áudio já está em um local acessível ou vou usar um mock de áudio do GCS.
    
    # IMPORTANTE: Para este teste, vamos assumir que o áudio 'cris_fala.mp3' 
    # foi enviado para um bucket público para a API conseguir buscar.
    AUDIO_URL = "https://storage.googleapis.com/brasil-ai-avatars/audios/cris_fala_demo.mp3"
    
    # Payload idêntico ao do D-ID
    payload = {
        "presenter_id": "cris_ai_avatar",
        "script": {
            "type": "audio",
            "audio_url": AUDIO_URL
        }
    }

    print(f"\n1. Enviando pedido para o Motor Industrial ({API_URL})...")
    try:
        response = requests.post(f"{API_URL}/clips", json=payload, timeout=60)
        
        if response.status_code not in [200, 201]:
            print(f"[ERROR] Erro na API: {response.text}")
            return
            
        job_id = response.json().get("id")
        print(f"[OK] Job Criado: {job_id}")
        
    except Exception as e:
        print(f"[ERROR] Nao foi possivel conectar ao servidor: {e}")
        print("💡 Verifique se você rodou 'ligar_lana.bat' e aguardou 1 minuto.")
        return
    
    # 2. Polling
    print(f"\n2. Aguardando processamento na GPU L4 ({job_id})...")
    
    status = "created"
    while status in ["created", "processing"]:
        time.sleep(5)
        try:
            res = requests.get(f"{API_URL}/clips/{job_id}", timeout=20)
            if res.status_code == 200:
                data = res.json()
                status = data.get("status")
                print(f"   [WAIT] Status: {status}")
                
                if status == "done":
                    video_url = data.get("result_url")
                    print(f"\n{GREEN}--- VIDEO COMPLETO! ---{END}")
                    
                    # 3. Baixar localmente
                    local_path = os.path.join(LOCAL_OUTPUT_DIR, f"cris_demo_{job_id}.mp4")
                    print(f"📥 Baixando para: {local_path}")
                    video_data = requests.get(video_url).content
                    with open(local_path, "wb") as f:
                        f.write(video_data)
                    print(f"\n[OK] Demo concluida com sucesso!")
                    return
                elif status == "error":
                    print(f"[ERROR] Erro: {data.get('error')}")
                    return
        except:
            print("   [WARNING] Aguardando resposta do server...")

if __name__ == "__main__":
    run_cris_demo()
