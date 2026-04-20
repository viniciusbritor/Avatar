from agno.agent import Agent
from agno.models.google import Gemini
from agente_lana_orchestrator import AgenteLanaOrchestrator
from secrets_manager import get_secret
import os
from dotenv import load_dotenv

load_dotenv()

# Injeta a chave do cofre no ambiente para o Agno/Gemini
os.environ["GOOGLE_API_KEY"] = get_secret("GEMINI_API_KEY")

class LanaOverlordV12:
    def __init__(self):
        self.orchestrator = AgenteLanaOrchestrator()
        
        # O Agente agora tem ferramentas industriais puras
        self.agent = Agent(
            name="Lana Overlord V12",
            model=Gemini(id="gemini-flash-latest"),
            description="Você é o Overlord Industrial do projeto Avatar. Sua única missão é produzir avatares no GCP com custo zero de ociosidade.",
            instructions=[
                "1. Receba o texto/áudio do usuário e acione a produção industrial.",
                "2. Você DEVE usar o presenter_id oficial da Lana: 'v2_public_lana_black_suite_green_screen@BTQAFVuIxZ'.",
                "3. Você DEVE garantir que a máquina seja desligada após o render para economizar recursos.",
                "4. Informe ao usuário o tempo gasto e o status da economia de recursos.",
                "5. Mantenha o foco absoluto no projeto Avatar."
            ],
            tools=[self.orchestrator.produce_video],
            debug_mode=True,
            markdown=True
        )

    def run(self, prompt: str):
        print(f"🧠 [OVERLORD V12] Processando comando: {prompt}")
        return self.agent.run(prompt)

if __name__ == "__main__":
    overlord = LanaOverlordV12()
    # Exemplo: overlord.run("Produza o vídeo da Cris com a frase padrão")
