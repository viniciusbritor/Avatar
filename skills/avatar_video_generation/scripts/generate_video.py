import requests
import json
import time

import base64

RAW_KEY = "dmluaWNpdXNicml0b3JAZ21haWwuY29t:jYq4FSnw268wbz_X7FZ8z"
API_KEY = base64.b64encode(RAW_KEY.encode()).decode()
PRESENTER_ID = "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"
SCRIPT = "Olá! Seja bem-vindo ao BrasilIA. Hoje trazemos as últimas atualizações sobre as decisões no Supremo Tribunal Federal que impactam diretamente o cenário político nacional. Fique ligado para conferir agora todos os detalhes e os bastidores desta notícia de última hora."

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
        "presenter_id": PRESENTER_ID
    }
    
    print(f"Enviando pedido para D-ID...")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        print(f"Erro: {response.status_code} - {response.text}")
        return
        
    data = response.json()
    clip_id = data['id']
    print(f"Pedido enviado! Clip ID: {clip_id}")
    
    # Poll for result
    while True:
        print("Aguardando processamento...")
        time.sleep(5)
        res = requests.get(f"{url}/{clip_id}", headers=headers)
        res_data = res.json()
        if res_data.get('status') == 'done':
            print(f"Pronto! URL: {res_data['result_url']}")
            return res_data['result_url']
        elif res_data.get('status') == 'error':
            print(f"Erro no processamento: {res_data}")
            return None

if __name__ == "__main__":
    url = generate()
    if url:
        with open('lana_output_url.txt', 'w') as f:
            f.write(url)
