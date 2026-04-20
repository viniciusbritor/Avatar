from agno.agent import Agent
from agno.models.google import Gemini
from agente_lana_orchestrator import AgenteLanaOrchestrator
from secrets_manager import get_secret
import os
from dotenv import load_dotenv

load_dotenv()

# Injeta a chave do cofre no ambiente para o SDK do Gemini
os.environ["GOOGLE_API_KEY"] = get_secret("GEMINI_API_KEY")

class AvatarOverlord:
    def __init__(self):
        self.orchestrator = AgenteLanaOrchestrator()
        
        self.agent = Agent(
            name="Lana Overlord",
            model=Gemini(id="gemini-1.5-flash"),
            description="Você é o Overlord do ecossistema Avatar Lana. Sua missão é gerenciar a produção de vídeos com o menor custo possível no GCP.",
            instructions=[
                "1. Quando receber um pedido de vídeo (texto e áudio), use o orquestrador para iniciar a produção.",
                "2. Você tem autonomia total para escolher a região e o hardware (L4 ou T4) visando economia.",
                "3. Após a produção, informe ao usuário o custo estimado do job e onde o arquivo foi salvo.",
                "4. Se houver falha em uma região barata, tente outra automaticamente sem perguntar.",
                "5. Mantenha um tom profissional, eficiente e focado em ROI (Retorno sobre Investimento)."
            ],
            tools=[self.orchestrator.run_production_cycle],
            debug_mode=True,
            markdown=True
        )

    def process_request(self, user_prompt: str):
        """Ponto de entrada para o agente processar pedidos de avatar."""
        return self.agent.run(user_prompt)

if __name__ == "__main__":
    # Exemplo de uso autonomo
    overlord = AvatarOverlord()
    # overlord.process_request("Gere um vídeo com o áudio assets/sarah_v2.mp3 usando o template lana_intro")
    print("🧠 Overlord Agent inicializado e pronto para comando.")
