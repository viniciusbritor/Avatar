import requests
import json
import time
import base64

# Credenciais do usuário (extraídas do script original)
RAW_KEY = "dmluaWNpdXNicml0b3JAZ21haWwuY29t:jYq4FSnw268wbz_X7FZ8z"
API_KEY = base64.b64encode(RAW_KEY.encode()).decode()
PRESENTER_ID = "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"
SCRIPT = "Eu sou seu avatar."

def generate():
    url = "https://api.d-id.com/clips"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {
            "type": "text",
            "input": SCRIPT,
            "provider": {"type": "microsoft", "voice_id": "pt-BR-FranciscaNeural"}
        },
        "presenter_id": PRESENTER_ID,
        "config": {
            "sharpen": True,
            "stitch": True
        }
    }
    
    print(f"🎬 Solicitando demo para D-ID (Lana)...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print(f"❌ Erro: {response.status_code} - {response.text}")
        return
        
    data = response.json()
    clip_id = data['id']
    print(f"🚀 Pedido enviado! Clip ID: {clip_id}")
    
    # Polling
    for _ in range(30):
        time.sleep(5)
        res = requests.get(f"{url}/{clip_id}", headers=headers)
        res_data = res.json()
        status = res_data.get('status')
        print(f"⏳ Status: {status}...")
        if status == 'done':
            print(f"\n✅ PRONTO! Link do vídeo: {res_data['result_url']}")
            return res_data['result_url']
        elif status == 'error':
            print(f"❌ Erro no processamento: {res_data}")
            return None
    
    print("❌ Tempo limite excedido.")
    return None

if __name__ == "__main__":
    generate()
