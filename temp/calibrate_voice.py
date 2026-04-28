import requests
import os
import subprocess
from secrets_manager import get_secret

ELEVENLABS_API_KEY = get_secret("ELEVEN_LABS_API_KEY")
TEXT = "Eu sou um avatar, isso é um teste de número dezoito."

configs = [
    {
        "name": "01_multilingual_v2_sarah_v1",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "model_id": "eleven_multilingual_v2",
        "stability": 0.40,
        "similarity_boost": 0.90,
        "style": 0.20,
        "atempo": 1.18
    },
    {
        "name": "02_turbo_v2.5_sarah_v2",
        "voice_id": "XrExE9yKIg1WjnnlVkGX",
        "model_id": "eleven_turbo_v2_5",
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.50,
        "atempo": 1.12
    },
    {
        "name": "03_multilingual_v2_sarah_v2",
        "voice_id": "XrExE9yKIg1WjnnlVkGX",
        "model_id": "eleven_multilingual_v2",
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.50,
        "atempo": 1.12
    }
]

os.makedirs("temp_audio", exist_ok=True)

for conf in configs:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{conf['voice_id']}"
    headers = {
        "Accept": "audio/mpeg", 
        "Content-Type": "application/json", 
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": TEXT,
        "model_id": conf['model_id'],
        "voice_settings": {
            "stability": conf['stability'],
            "similarity_boost": conf['similarity_boost'],
            "style": conf['style'],
            "use_speaker_boost": True
        }
    }
    
    print(f"Gerando {conf['name']}...")
    res = requests.post(url, json=data, headers=headers)
    if res.status_code == 200:
        base_path = f"temp_audio/{conf['name']}.mp3"
        with open(base_path, 'wb') as f:
            f.write(res.content)
            
        fast_path = f"temp_audio/{conf['name']}_fast.mp3"
        subprocess.run(["ffmpeg", "-y", "-i", base_path, "-filter:a", f"atempo={conf['atempo']}", fast_path], capture_output=True)
        print(f"✅ Salvo: {fast_path}")
    else:
        print(f"❌ Erro em {conf['name']}: {res.text}")
