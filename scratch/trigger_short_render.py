import requests
import json

url = "http://localhost:8080/clips"
data = {
    "presenter_id": "lana_intro",
    "script": {
        "type": "audio",
        "audio_url": "gs://brasil-ai-avatars/inputs/oi_sou_a_cris_v2.mp3"
    },
    "resolution": 512
}

try:
    print(f"Enviando request para {url} (com GCS URI)...")
    r = requests.post(url, json=data)
    print(f"Status: {r.status_code}")
    print(f"Resposta: {r.text}")
except Exception as e:
    print(f"Error: {e}")
