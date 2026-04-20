import requests
import os
from dotenv import load_dotenv

# Configurações ElevenLabs
VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Sarah (Correta)
API_KEY = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"

TEXT_INTRO = "A Ministra Cármen Lúcia, presidente do TSE, surpreendeu o Brasil ao renunciar antecipadamente ao comando da Corte Eleitoral. O fato central é a entrega do Tribunal Superior Eleitoral ao Ministro Kassio Nunes Marques meses antes do previsto, reconfigurando a liderança das próximas eleições municipais. Este movimento abrupto sinaliza profundas dissidências no Supremo Tribunal Federal, gerando instabilidade política."
TEXT_OUTRO = "A posse de Kassio Nunes no TSE expõe a fratura no judiciário. Curta, compartilhe e inscreva-se no Brasil Ei-Ai para mais análises. Até a próxima!"

def generate_audio(text, filename):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Audio salvo: {filename}")
    else:
        print(f"Erro ElevenLabs: {response.text}")

print("Gerando audios da Cris (Sarah)...")
generate_audio(TEXT_INTRO, "c:\\Users\\vinic\\workspace_antigravity\\Avatar\\cris_intro_audio.mp3")
generate_audio(TEXT_OUTRO, "c:\\Users\\vinic\\workspace_antigravity\\Avatar\\cris_outro_audio.mp3")
