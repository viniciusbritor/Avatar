from flask import Flask, request
import subprocess
import os
from datetime import datetime
import sys

# Garante UTF-8 no print
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# Caminhos
BATCH_SCRIPT = "scripts/batch_upload_pending.py"
LOG_FILE = "webhook_log.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(full_msg + "\n")

@app.route('/gmail-trigger', methods=['POST'])
def gmail_trigger():
    log("RECEPTOR: Sinal do Gmail recebido via POST!")
    
    try:
        log("RECEPTOR: Disparando motor de upload...")
        subprocess.Popen(["python", BATCH_SCRIPT])
        return {"status": "success", "message": "Iniciado com sucesso!"}, 200
    except Exception as e:
        log(f"RECEPTOR: Erro ao disparar: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return "Webhook Receptor Brasil AI is LIVE!", 200

if __name__ == '__main__':
    log("RECEPTOR: Iniciado na porta 5000.")
    app.run(port=5000)
