from overlord_agent_v12 import LanaOverlordV12
import os

def final_mission():
    print("🚀 [FINAL MISSION] Ativando Overlord V12 para o render industrial...")
    audio = "c:/Users/vinic/workspace_antigravity/Avatar/audio_cris_v2_ptbr.mp3"
    prompt = f"Lana, produza o vídeo final da Cris com o áudio {audio}. Após o sucesso, certifique-se de que a máquina foi desligada."
    
    overlord = LanaOverlordV12()
    overlord.run(prompt)

if __name__ == "__main__":
    final_mission()
