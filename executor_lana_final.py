from agente_lana_orchestrator import AgenteLanaOrchestrator
from secrets_manager import get_secret
import os

def final_production():
    print("🚀 [DIRECT] Disparando produção direta na Engine Industrial...")
    
    # Injeta a chave do cofre no ambiente
    os.environ["GOOGLE_API_KEY"] = get_secret("GEMINI_API_KEY")
    
    # Parâmetros oficiais de alta fidelidade
    audio_file = "c:/Users/vinic/workspace_antigravity/Avatar/audio_cris_v2_ptbr.mp3"
    presenter_id = "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"
    
    orchestrator = AgenteLanaOrchestrator()
    # Executa o ciclo de produção diretamente nos motores da Virginia
    result = orchestrator.run_production_cycle(audio_path=audio_file, presenter_id=presenter_id)
    
    print("\n" + "="*50)
    print("📜 RESULTADO DA PRODUÇÃO INDUSTRIAL:")
    print(result)
    print("="*50)

if __name__ == "__main__":
    final_production()
