import requests
import os

API_KEY = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL" # Sarah (Official Project Standard)
TEXT = "Ola eu sou a Cris, esse é o Brasil EiAI e hoje eu vou explicar toda a política do Brasil para vc!"
OUTPUT_PATH = "c:/Users/vinic/workspace_antigravity/Avatar/lana_audio_v7.mp3"

def generate_audio():
    print(f"--- [ELEVENLABS] Gerando audio oficial para: '{TEXT}' ---")
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
            "stability": 0.50,
            "similarity_boost": 0.80
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(OUTPUT_PATH, 'wb') as f:
            f.write(response.content)
            
        # OTIMIZAÇÃO: Acelerar 12% para o ritmo "Lana" (Soberania)
        import subprocess
        print("--- [FFMPEG] Aplicando aceleracao industrial (1.12x)... ---")
        fast_path = OUTPUT_PATH.replace(".mp3", "_fast.mp3")
        subprocess.run(["ffmpeg", "-y", "-i", OUTPUT_PATH, "-filter:a", "atempo=1.12", fast_path], capture_output=True)
        if os.path.exists(fast_path):
            os.replace(fast_path, OUTPUT_PATH)
            
        print(f"DONE: Audio industrial pronto em: {OUTPUT_PATH}")
    else:
        print(f"FAILED: Erro na API ElevenLabs: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    generate_audio()
