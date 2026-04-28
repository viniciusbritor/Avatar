import time
import sys
import os

# Adicionar o diretório src ao path para importar o orquestrador
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "src")))

from agente_lana_orchestrator import LanaIndustrialEngine

def test_t4_failover():
    print("[TEST] Iniciando Simulação de Failover para T4...")
    engine = LanaIndustrialEngine()
    
    # MOCK: Esvaziar a lista de zonas L4 para forçar o failover para T4
    print("[MOCK] Desativando zonas L4 para forçar Plan B (T4)...")
    engine.l4_zones = [] 
    
    # MOCK: Reduzir zonas T4 para apenas uma conhecida (us-east1-b ou similar)
    # us-east1-b costuma ter T4 disponível
    # engine.t4_zones = ["us-central1-a"] # Let it search all zones
    
    try:
        def log_progress(msg):
            print(f"  > {msg}")
            
        print("[TEST] Solicitando instância industrial...")
        ip = engine.ensure_instance_ready(progress_callback=log_progress)
        print(f"[SUCCESS] Instância provisionada com sucesso no IP: {ip}")
        print(f"[INFO] Tipo de GPU Ativo: {engine.current_gpu_type}")
        print(f"[INFO] Nome da Instância: {engine.active_instance}")
        
        if engine.current_gpu_type == "T4":
            print("[VERIFIED] Failover para T4 funcionou corretamente!")
        else:
            print("[FAILED] O orquestrador não usou T4 como esperado.")
            
    except Exception as e:
        print(f"[CRITICAL] Erro no teste de failover: {e}")
    finally:
        # Limpeza (Zero-Waste)
        if engine.active_instance:
            print(f"[CLEANUP] Removendo instância de teste: {engine.active_instance}")
            engine._purge_zone(engine.active_instance, engine.active_zone)

if __name__ == "__main__":
    test_t4_failover()
