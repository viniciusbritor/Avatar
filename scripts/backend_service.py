import os
import time
import subprocess
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime

# Configurações
TOKEN_FILE = "token_master_full.json"
BATCH_SCRIPT = "scripts/batch_upload_pending.py"
LOG_FILE = "brasil_ai_backend.log"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(full_msg + "\n")

def check_for_approval():
    if not os.path.exists(TOKEN_FILE):
        return False
        
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
            
    service = build('gmail', 'v1', credentials=creds)
    
    # Query específica para o e-mail de aprovação
    query = 'from:(google.com OR youtube.com) "recursos avançados" OR "advanced features"'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    return len(messages) > 0

def run_service():
    log("SISTEMA BACKEND BRASIL AI: Iniciado e monitorando...")
    
    # Marcador para não repetir o processo se já disparou
    has_triggered = False
    
    while True:
        try:
            # Se já disparou, podemos diminuir a frequência ou parar
            if not has_triggered:
                if check_for_approval():
                    log("!!! APROVAÇÃO DETECTADA NO GMAIL !!!")
                    log("Iniciando upload das pautas pendentes...")
                    subprocess.run(["python", BATCH_SCRIPT])
                    has_triggered = True
                    log("Upload concluído. Sistema em espera para novas pautas.")
                else:
                    # Log silencioso para não encher o disco, apenas a cada 10 ciclos
                    pass 
            
        except Exception as e:
            log(f"Erro no ciclo de monitoramento: {e}")
            
        # Checa a cada 60 segundos
        time.sleep(60)

if __name__ == "__main__":
    run_service()
