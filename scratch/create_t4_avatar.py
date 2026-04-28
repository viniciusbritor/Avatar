import sys
import os

# Adiciona o path do src para importar o orquestrador
sys.path.append(os.path.join(os.getcwd(), 'src'))

from agente_lana_orchestrator import AgenteLanaOrchestrator

def create_t4_avatar():
    text = "Esse é o teste 16 usando uma maquina T4"
    print(f"🎬 INICIANDO PRODUÇÃO DE AVATAR (T4 ARCHITECTURE)")
    print(f"📝 Texto: {text}")
    
    maestro = AgenteLanaOrchestrator()
    
    # Força o uso da arquitetura T4 para validar o Plano B
    res = maestro.produce_video_from_text(text, force_gpu="T4")
    
    if res["status"] == "success":
        print(f"\n🎉 SUCESSO! Avatar criado com sucesso usando a infra T4.")
        print(f"🎥 Caminho do vídeo: {res['video_path']}")
    else:
        print(f"\n❌ FALHA na produção: {res['message']}")

if __name__ == "__main__":
    create_t4_avatar()
