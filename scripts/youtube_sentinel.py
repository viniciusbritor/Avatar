import time
import os
import subprocess
from datetime import datetime

# Configurações
CHECK_INTERVAL = 3600  # 1 hora em segundos
BATCH_SCRIPT = "scripts/batch_upload_pending.py"
LOG_FILE = "sentinel_log.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(full_msg + "\n")

def start_sentinel():
    log("🎥 Agente Sentinela Brasil AI Iniciado. Monitorando liberacao do canal...")
    
    while True:
        log("🔍 Verificando status de upload no YouTube...")
        
        # Tenta rodar o lote
        process = subprocess.run(["python", BATCH_SCRIPT], capture_output=True, text=True, encoding='utf-8')
        output = process.stdout + process.stderr
        
        if "uploadLimitExceeded" in output:
            log("❌ Canal ainda bloqueado. Próxima tentativa em 1 hora.")
        elif "Sucesso" in output:
            log("🚀 SUCESSO! Videos postados. O limite foi liberado.")
            # Se postou tudo com sucesso, podemos parar ou continuar monitorando novas pautas
            if "Nenhuma pauta pendente" in output:
                log("✅ Fila limpa. Sentinela em modo de espera.")
        else:
            log(f"⚠️ Status inesperado ou fila vazia: {output[:100]}...")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    start_sentinel()
