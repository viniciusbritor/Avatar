import os
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_sarah_v2():
    api_key = os.getenv('ELEVEN_API_KEY')
    if not api_key:
        print("Error: ELEVEN_API_KEY not found in .env")
        return

    voice_id = "EXAVITQu4vr4xnSDxMaL"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Parametros otimizados V9.4 - Alta Fidelidade
    data = {
        "text": "Eu sou uma menina que faz o que bem entende!",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }
    
    print("Iniciando sintese Premium via REST API (Sarah V2)...")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            output_path = "sarah_v2.mp3"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Sucesso: Audio salvo em {output_path}")
        else:
            print(f"Erro na API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro de rede: {e}")

if __name__ == "__main__":
    generate_sarah_v2()
