import subprocess
import time
import sys
import os

def start_system():
    print("--- Iniciando Sistema de Reacao Instantanea Brasil AI ---")
    
    # 1. Inicia o Flask em background
    print("[1] Subindo receptor Flask...")
    flask_proc = subprocess.Popen(["python", "scripts/webhook_receptor.py"])
    
    time.sleep(3) # Espera o Flask subir
    
    # 2. Inicia o Localtunnel
    subdomain = "brasil-ai-trigger"
    print(f"[2] Abrindo tunel publico em: https://{subdomain}.loca.lt")
    
    # Comando localtunnel
    lt_cmd = f"lt --port 5000 --subdomain {subdomain}"
    
    try:
        subprocess.run(lt_cmd, shell=True)
    except KeyboardInterrupt:
        print("\n--- Encerrando sistema ---")
        flask_proc.terminate()

if __name__ == "__main__":
    start_system()
