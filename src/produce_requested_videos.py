import sys
import os
from agente_lana_orchestrator import AgenteLanaOrchestrator

def main():
    orchestrator = AgenteLanaOrchestrator()
    
    scripts = [
        "Eu sou um avatar, isso é um teste de número 18."
    ]
    
    print(f"--- [BRASIL AI] Iniciando produção de {len(scripts)} vídeos ---")
    
    results = []
    for i, script in enumerate(scripts, 1):
        print(f"\n--- [VIDEO {i}/{len(scripts)}] Produzindo: '{script[:30]}...' ---")
        result = orchestrator.produce_video_from_text(script, index=i, total=len(scripts))
        results.append(result)
        
        if result["status"] == "success":
            print(f"✅ Vídeo {i} concluído: {result['video_path']}")
        else:
            print(f"❌ Falha no Vídeo {i}: {result['message']}")
            
    print("\n--- [FINALIZADO] Resumo da Produção ---")
    for i, res in enumerate(results, 1):
        status = "✅ SUCESSO" if res["status"] == "success" else "❌ ERRO"
        path_or_msg = res.get("video_path") or res.get("message")
        print(f"Vídeo {i}: {status} - {path_or_msg}")

    print("\n[FINOPS] Encerrando máquina para evitar custos ociosos...")
    try:
        if orchestrator.engine.active_instance and orchestrator.engine.active_zone:
            orchestrator.engine._purge_zone(orchestrator.engine.active_instance, orchestrator.engine.active_zone)
            print("[FINOPS] Máquina deletada com sucesso. Zero-Waste atingido.")
    except Exception as e:
        print(f"[FINOPS WARNING] Erro ao deletar máquina: {e}")

if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), "src"))
    main()
