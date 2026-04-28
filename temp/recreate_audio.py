import requests
import os
import subprocess
import time
from secrets_manager import get_secret

ELEVENLABS_API_KEY = get_secret("ELEVEN_LABS_API_KEY")
TEXT = "Essa não é apenas uma questão interna, é um contorcionismo jurídico que expõe o Brasil a sanções duríssimas, inclusive afetando o Pix e acordos com a China. O STF entende o perigo?"
VOICE_ID = "XrExE9yKIg1WjnnlVkGX"

print("1. Gerando com XrExE9yKIg1WjnnlVkGX + multilingual_v2 + sem atempo")
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
with open("test_audio_custom_sarah.mp3", 'wb') as f:
    f.write(res.content)

print("Audio salvo. Extraindo duração:")
subprocess.run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 test_audio_custom_sarah.mp3", shell=True)

# Testando com a aceleração original do pipeline
print("Aplicando atempo 1.12...")
subprocess.run("ffmpeg -y -i test_audio_custom_sarah.mp3 -filter:a atempo=1.12 test_audio_custom_sarah_fast.mp3", shell=True)
subprocess.run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 test_audio_custom_sarah_fast.mp3", shell=True)
