import subprocess
import time
import logging

# Configuracoes do Watchdog
IDLE_LIMIT_MINUTES = 30
CHECK_INTERVAL_SECONDS = 300 # 5 minutos

logging.basicConfig(filename='/tmp/overlord_watchdog.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

def get_gpu_usage():
    """Verifica utilizacao da GPU via nvidia-smi."""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                capture_output=True, text=True)
        return int(result.stdout.strip())
    except:
        return 0

def get_container_status():
    """Verifica se o container lana-engine esta rodando processos pesados."""
    try:
        result = subprocess.run(['sudo', 'docker', 'stats', '--no-stream', '--format', '{{.CPUPerc}}', 'lana-engine'],
                                capture_output=True, text=True)
        cpu_val = float(result.stdout.strip().replace('%', ''))
        return cpu_val
    except:
        return 0

def main():
    idle_count = 0
    logging.info("🕵️ Watchdog Overlord iniciado. Proteção de custos ativa.")
    
    while True:
        gpu_usage = get_gpu_usage()
        cpu_usage = get_container_status()
        
        logging.info(f"Monitorando - GPU: {gpu_usage}% | CPU Container: {cpu_usage}%")
        
        # Se GPU < 5% e CPU < 10% (Indice de ociosidade)
        if gpu_usage < 5 and cpu_usage < 10:
            idle_count += 5
            logging.warning(f"Ociosidade detectada! Acumulado: {idle_count}/{IDLE_LIMIT_MINUTES} min")
        else:
            if idle_count > 0:
                logging.info("Atividade detectada. Resetando contador de ociosidade.")
            idle_count = 0
            
        if idle_count >= IDLE_LIMIT_MINUTES:
            logging.critical("LIMITE DE OCIOSIDADE ATINGIDO. Iniciando desligamento de emergência para economizar custos.")
            subprocess.run(['sudo', 'poweroff'])
            break
            
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
