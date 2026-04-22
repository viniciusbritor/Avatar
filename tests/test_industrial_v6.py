import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from agente_lana_orchestrator import LanaIndustrialEngine

def test_final_industrial_pipeline():
    print("--- INICIANDO TESTE DE PRODUCAO INDUSTRIAL V6 ---")
    orchestrator = LanaIndustrialEngine()
    
    # Teste de ponta a ponta
    test_text = "Teste final do motor industrial v6. Orquestracao completa, imagem gold registrada e entrega local validada. O sistema esta pronto para escala."
    
    print(f"Texto do teste: {test_text}")
    result = orchestrator.produce_video_from_text(test_text)
    
    if result["status"] == "success":
        print(f"\n[SUCESSO TOTAL!]")
        print(f"Video entregue em: {result['video_path']}")
    else:
        print(f"\n[FALHA NO TESTE]: {result['message']}")

if __name__ == "__main__":
    test_final_industrial_pipeline()
