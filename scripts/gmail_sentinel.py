import os
import json
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import subprocess
from datetime import datetime

# Configuracoes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token_master_full.json"
CHECK_INTERVAL = 300  # 5 minutos
BATCH_SCRIPT = "scripts/batch_upload_pending.py"
LOG_FILE = "gmail_sentinel_log.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(full_msg + "\n")

def check_gmail():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
            
    service = build('gmail', 'v1', credentials=creds)
    
    # Busca por e-mail de recursos avancados ou fim de limite
    # Query: e-mails do youtube/google sobre recursos ou aprovacao
    query = 'from:(google.com OR youtube.com) "recursos avançados" OR "advanced features"'
    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    messages = results.get('messages', [])
    
    return len(messages) > 0

def run_sentinel():
    log("📧 Sentinela Gmail Brasil AI Ativado. Monitorando sua caixa de entrada...")
    last_count = 0
    
    # Primeira checagem para saber o estado atual
    try:
        last_count = 1 if check_gmail() else 0
    except Exception as e:
        log(f"Erro na conexao Gmail: {e}")

    while True:
        try:
            log("🔎 Verificando e-mails...")
            if check_gmail():
                log("🎯 E-mail de liberacao detectado! Iniciando uploads represados...")
                subprocess.run(["python", BATCH_SCRIPT])
                log("✅ Processamento concluido. Sentinela continua em vigilia.")
                # Opcional: break se quiser que ele pare apos o primeiro sucesso total
            else:
                log("🧊 Nenhum e-mail de liberacao novo encontrado.")
        except Exception as e:
            log(f"Erro no ciclo: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_sentinel()
