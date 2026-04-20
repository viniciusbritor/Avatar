import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configurações da ElevenLabs
API_KEY = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah (Correto para Cris/Lana)

TEXT = "Oi! Eu sou a Cris."
OUTPUT_PATH = r"c:\Users\vinic\workspace_antigravity\Avatar\demo_results\oi_sou_a_cris.mp3"

def generate_audio():
    print(f"Gerando áudio para: {TEXT}")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": TEXT,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(OUTPUT_PATH, "wb") as f:
            f.write(response.content)
        print(f"Áudio salvo em: {OUTPUT_PATH}")
        return True
    else:
        print(f"Erro ElevenLabs: {response.text}")
        return False

if __name__ == "__main__":
    generate_audio()
