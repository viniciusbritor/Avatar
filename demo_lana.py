import requests
import subprocess
import time
import os
import json

def get_google_auth_token():
    """Obtem token do gcloud caso o server exija (RunPod pode usar tokens próprios ou nenhum)."""
    try:
        return subprocess.check_output(['gcloud', 'auth', 'print-identity-token'], text=True, shell=True).strip()
    except:
        return None

def download_video_local(url, dest_path):
    print(f"📥 Baixando vídeo final: {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print("✅ Download concluído!")
        else:
            print(f"❌ Falha no download. Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Erro no download: {e}")

def run_mirror_demo():
    # URL da sua nova API no RunPod (exemplo)
    API_URL = "https://your-runpod-id-8080.proxy.runpod.net"
    LOCAL_OUTPUT_DIR = "demo_results"
    os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
    
    print("--- 🎭 D-ID Mirror Demo (Lana Avatar) ---")
    
    # Payload idêntico ao do D-ID que o LangGraph envia
    payload = {
        "presenter_id": "v2_public_lana_black_suite_green_screen",
        "script": {
            "type": "audio",
            "audio_url": "https://storage.googleapis.com/brasil-ai-avatars/audios/lana_welcome.mp3"
        }
    }

    # 1. POST /clips (Criação)
    print("\n1. Criando Clip via Emulador...")
    response = requests.post(f"{API_URL}/clips", json=payload, timeout=60)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Erro na API: {response.text}")
        return
        
    job_id = response.json().get("id")
    print(f"✅ Job Criado: {job_id}")
    
    # 2. GET /clips/{id} (Polling)
    print("\n2. Aguardando processamento na GPU L4 (Polling)...")
    
    status = "created"
    while status in ["created", "processing"]:
        time.sleep(5)
        res = requests.get(f"{API_URL}/clips/{job_id}", timeout=20)
        
        if res.status_code == 200:
            data = res.json()
            status = data.get("status")
            print(f"   ⏳ Status: {status}")
            
            if status == "done":
                video_url = data.get("result_url")
                print(f"\n🎉 VÍDEO PRONTO!")
                
                # 3. Entrega Local
                local_path = os.path.join(LOCAL_OUTPUT_DIR, f"lana_{job_id}.mp4")
                download_video_local(video_url, local_path)
                return
            elif status == "error":
                print(f"❌ Erro no Worker: {data.get('error')}")
                return
        else:
            print("⚠️ Erro ao checar status. Tentando novamente...")

if __name__ == "__main__":
    run_mirror_demo()
