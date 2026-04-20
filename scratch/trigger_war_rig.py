import requests
import json
import time

url = "http://localhost:8080/clips"
payload = {
    "script": {
        "type": "audio",
        "audio_url": "gs://brasil-ia-lana-assets/audios/audio_cris_v2_ptbr.mp3"
    },
    "presenter_id": "lana_intro"
}

print(f"🚀 [LOCAL] Disparando renderizacao SOBERANA para: {payload['script']['audio_url']}...")
try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"✅ [API] Resposta: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"❌ [ERRO] Falha ao disparar API: {e}")
