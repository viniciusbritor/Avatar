import requests
import os
from secrets_manager import get_secret

ELEVENLABS_API_KEY = get_secret("ELEVEN_LABS_API_KEY")
TEXT = "Eu sou um avatar, isso é um teste de número 18."
VOICE_ID = "XrExE9yKIg1WjnnlVkGX"

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "Accept": "audio/mpeg", 
    "Content-Type": "application/json", 
    "xi-api-key": ELEVENLABS_API_KEY
}
data = {
    "text": TEXT,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.50,
        "use_speaker_boost": True
    }
}
res = requests.post(url, json=data, headers=headers)

output_file = r"c:\Users\vinic\workspace_antigravity\Avatar\temp\audio_teste_18.mp3"
os.makedirs(os.path.dirname(output_file), exist_ok=True)

if res.status_code == 200:
    with open(output_file, 'wb') as f:
        f.write(res.content)
    print(f"✅ Áudio isolado gerado com sucesso: {output_file}")
else:
    print(f"❌ Erro: {res.text}")
