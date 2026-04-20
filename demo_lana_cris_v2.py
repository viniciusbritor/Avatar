import os
import sys
from agente_lana_orchestrator import AgenteLanaOrchestrator
from skills.avatar_video_generation.scripts.elevenlabs_tts import generate_tts

def run_cris_v2_demo():
    print("🚀 Iniciando Produção Cris V2 (Diana + Sarah Brasil)...")
    
    # 1. Configurações de Voz (Sarah)
    texto = "Eu sou Cris, sou um mulher dificil e vou até o fim com o que acredito!"
    voice_id = "EXAVITQu4vr4xnSDxMaL" # Sarah Oficinal
    audio_output = "c:/Users/vinic/workspace_antigravity/Avatar/audio_cris_v2_ptbr.mp3"
    
    # 2. Geração do Áudio Exatamente como Sarah v2
    print("🎙️ Gerando áudio Sarah com sotaque Brasil nativo...")
    generate_tts(
        text=texto,
        output_path=audio_output,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "stability": 0.55,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True
        }
    )
    
    # 3. Identidade Visual (Diana)
    diana_id = "v2_public_diana@so9Pg73d6N"
    
    # 4. Acionamento do Orquestrador Industrial
    orch = AgenteLanaOrchestrator()
    orch.run_production_cycle(
        audio_path=audio_output,
        presenter_id=diana_id
    )

if __name__ == "__main__":
    run_cris_v2_demo()
