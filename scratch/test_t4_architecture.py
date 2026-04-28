import sys
import os
import time

# Adiciona o path do src para importar o orquestrador
sys.path.append(os.path.join(os.getcwd(), 'src'))

from agente_lana_orchestrator import LanaIndustrialEngine

def test_t4_infra():
    print("🚀 INICIANDO TESTE DE ARQUITETURA T4 (PLAN B)")
    engine = LanaIndustrialEngine()
    
    try:
        # Força o provisionamento da T4 ignorando a L4
        ip = engine.ensure_instance_ready(force_gpu="T4")
        
        if ip:
            print(f"✅ SUCESSO: Infraestrutura T4 pronta e operacional!")
            print(f"📍 IP da Máquina: {ip}")
            print(f"🛠️  Arquitetura: NVIDIA T4 (Plan B)")
            print(f"📦 Container: lana-v6-t4-industrial-v1")
            print("\nO ambiente está pronto para criar o avatar.")
        else:
            print("❌ FALHA: Não foi possível provisionar a T4 nas zonas testadas.")
            
    except Exception as e:
        print(f"💥 ERRO CRÍTICO NO TESTE: {e}")

if __name__ == "__main__":
    test_t4_infra()
