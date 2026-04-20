import sys
import os
from agente_lana_orchestrator import AgenteLanaOrchestrator

def run_test():
    phrase = "Olá eu sou a Cris do Brasil EiAi, vem aqui é dá uma moral para o Vinicius. Eu vou fazer ele ficar rico!"
    maestro = AgenteLanaOrchestrator()
    print(f"--- TESTE INDUSTRIAL LANA v2.0 ---")
    print(f"Texto: {phrase}")
    result = maestro.produce_video_from_text(phrase)
    print(f"Resultado: {result}")

if __name__ == "__main__":
    run_test()
