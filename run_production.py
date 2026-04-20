import os
import time
import requests
import subprocess
import json
import sys

# --- FINAL PRODUCTION CONFIGURATION ---
PROJECT_ID = "brasili-ia-news"
BUCKET_NAME = "brasil-ia-lana-assets"
INSTANCE_NAME = "lana-engine-v25-final-industrial"
ZONE = "us-east4-a"
ELEVENLABS_API_KEY = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Sarah Original (Natural)

MACHINE_IMAGE = "lana-engine-master-v31-gold-standard"
IDLE_TIMEOUT_MINUTES = 10

def ensure_infrastructure():
    print(f"[{time.strftime('%X')}] 1. Orquestrador Híbrido: Validando Infraestrutura...")
    cmd = f"gcloud compute instances describe {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --format=json"
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if res.returncode != 0:
        # Instância DELETADA ou não existe
        print(f"[{time.strftime('%X')}]    -> Ambiente inexistente! Criando nova VM a partir da Machine Image ({MACHINE_IMAGE})...")
        print(f"[{time.strftime('%X')}]    (Isso alocará a GPU e restaurará o disco bloqueado. Tempo estimado: 3 minutos).")
        create_cmd = f"gcloud compute instances create {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --source-machine-image={MACHINE_IMAGE} --metadata startup-script=\"\" --quiet"
        subprocess.run(create_cmd, shell=True, check=True)
        print(f"[{time.strftime('%X')}]    [OK] Ambiente restaurado e GPU Alocada.")
    else:
        info = json.loads(res.stdout)
        status = info.get("status")
        if status == "TERMINATED" or status == "STOPPED":
            print(f"[{time.strftime('%X')}]    -> Ambiente desligado. Iniciando cluster de GPU...")
            start_cmd = f"gcloud compute instances start {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --quiet"
            subprocess.run(start_cmd, shell=True, check=True)
            print(f"[{time.strftime('%X')}]    [OK] GPU Acordada.")
        elif status == "RUNNING":
            print(f"[{time.strftime('%X')}]    [OK] Infraestrutura de GPU já está online e operante.")

    # Pega o IP
    ip_cmd = f"gcloud compute instances describe {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --format=get(networkInterfaces[0].accessConfigs[0].natIP)"
    ip_r = subprocess.run(ip_cmd, capture_output=True, text=True, shell=True)
    vm_ip = ip_r.stdout.strip()
    
    # Cancela qualquer desligamento agendado previamente (extensão do Idle Timeout)
    print(f"[{time.strftime('%X')}]    -> Suspendendo timer de ociosidade...")
    cancel_cmd = f"gcloud compute ssh {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --tunnel-through-iap --command \"sudo shutdown -c\" --quiet"
    subprocess.run(cancel_cmd, capture_output=True, shell=True)
    
    return vm_ip

def generate_audio(text):
    print(f"[{time.strftime('%X')}] 2. Sintetizando Voz Neural HQ (Larissa Native)...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY}
    # V29: Increased stability for human-like prosody, removed robotic atempo
    data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.65, "similarity_boost": 0.80}}
    res = requests.post(url, json=data, headers=headers)
    if res.status_code == 200:
        with open("outputs/temp_prompt.mp3", 'wb') as f: f.write(res.content)
        return "outputs/temp_prompt.mp3"
    raise Exception(f"Erro TTS: {res.text}")

def upload_audio(local_path):
    print(f"[{time.strftime('%X')}] 3. Fazendo Upload de Ativos para GCP...")
    # V30: Unique key para forçar a GPU a ignorar o buffer de cache antigo
    unique_id = int(time.time())
    gcs_path = f"gs://{BUCKET_NAME}/temp/input_audio_{unique_id}.mp3"
    subprocess.run(["gsutil", "cp", local_path, gcs_path], capture_output=True, shell=True)
    return gcs_path.replace("gs://", "https://storage.googleapis.com/")

def produce_video(text):
    os.makedirs("outputs", exist_ok=True)
    
    # Executa Passos 1 a 3
    vm_ip = ensure_infrastructure()
    audio_path = generate_audio(text)
    public_url = upload_audio(audio_path)
    
    # Passo 4: Container já é iniciado automaticamente pelo startup.sh da VM
    # (não usamos SSH aqui pois o plink.exe do Windows fecha a conexão antes de terminar)
    print(f"[{time.strftime('%X')}] 4. Aguardando Motor Neural inicializar...")
    
    # Passo 5: Acoplar e Esperar Motor Acordar (Até 120s para instilação limpa do contêiner)
    print(f"[{time.strftime('%X')}] 5. Aguardando Health Check da API Neural...")
    api_ready = False
    for i in range(60):  # 60 * 5 = 300 segundos (5 min) para suportar subida a frio total
        try:
            h = requests.get(f"http://{vm_ip}:8080/health", timeout=5)
            if h.status_code == 200:
                api_ready = True
                print(f"[{time.strftime('%X')}]    [OK] API Online e Pronta!")
                break
        except Exception:
            sys.stdout.write(f"\r    -> Inicializando serviços internos... ({i*5}s)")
            sys.stdout.flush()
            time.sleep(5)
            
    if not api_ready:
        raise Exception("O contêiner falhou ao subir (verifique os logs internos).")
    sys.stdout.write("\n")

    print(f"[{time.strftime('%X')}] 6. Enviando Instrução de Renderização...")
    payload = {
        "presenter_id": "lana_intro",
        "script": {"type": "audio", "audio_url": public_url}
    }
    
    res = requests.post(f"http://{vm_ip}:8080/clips", json=payload, timeout=10)
    job_id = res.json().get("id")

    print(f"\n[{time.strftime('%X')}] 7. PROGRESSO DA ESTAÇÃO:")
    start_time = time.time()
    for _ in range(100): # Limite de seguranca de 25 min (100 * 15s)
        time.sleep(15)
        r = requests.get(f"http://{vm_ip}:8080/clips/{job_id}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            status = data.get("status")
            
            elapsed = int(time.time() - start_time)
            # Calculo de progresso visual simulado baseado no tempo medio vs elapsed
            progresso_visual = min(100, int((elapsed / 240) * 100)) if status == "processing" else 100
            bar_len = 40
            filled = int(bar_len * (progresso_visual / 100))
            bar = "#" * filled + "-" * (bar_len - filled)
            
            sys.stdout.write(f"\r |{bar}| {progresso_visual}% - [{status.upper()}] ({elapsed}s)")
            sys.stdout.flush()

            if status == "completed" or status == "completed_no_audio":
                sys.stdout.write("\n\n")
                print(f"[{time.strftime('%X')}] 7. SUCESSO! Baixando Vídeo Furtivamente...")
                
                # Baixar video gerado (local_path returned by python inside VM)
                remote_path = data.get("result_url")
                local_final = f"outputs/AVATAR_FINAL_{time.strftime('%Y%m%d_%H%M%S')}_{job_id[-6:]}.mp4"
                
                download_cmd = f"gcloud compute scp {INSTANCE_NAME}:{remote_path} {local_final} --project {PROJECT_ID} --zone {ZONE} --tunnel-through-iap --quiet"
                subprocess.run(download_cmd, shell=True)
                
                print(f"[{time.strftime('%X')}] ==========================")
                print(f"VIDEO ENTREGUE: {os.path.abspath(local_final)}")
                print(f"[{time.strftime('%X')}] ==========================")
                
                # Desligamento Automático (FinOps) agendado nativamente no linux da VM!
                print(f"[{time.strftime('%X')}] 8. Programando Desligamento de Ociosidade (FinOps: {IDLE_TIMEOUT_MINUTES} min)...")
                shutdown_cmd = f"gcloud compute ssh {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --tunnel-through-iap --command \"sudo shutdown -h +{IDLE_TIMEOUT_MINUTES}\" --quiet"
                subprocess.run(shutdown_cmd, capture_output=True, shell=True)

                return local_final
            elif status == "error":
                sys.stdout.write("\n")
                raise Exception(f"Erro no Motor GCP: {data.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        texto = " ".join(sys.argv[1:])
    else:
        texto = "Olá! O pipeline de produção está operando na sua versão máxima. A infraestrutura de GPU agora está perfeitamente sincronizada em minutos."
    produce_video(texto)
