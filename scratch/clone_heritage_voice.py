import requests

# ElevenLabs API Config
api_key = "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901"
url = "https://api.elevenlabs.io/v1/voices/add"
headers = {"xi-api-key": api_key}

data = {
    "name": "Cris Soberana Heritage v13",
    "description": "Customização exata da Sarah v13 Heritage para o projeto industrial Lana."
}

# Path to the extracted perfect audio
file_path = r"c:\Users\vinic\workspace_antigravity\Avatar\scratch\audio_v13_reference.mp3"

try:
    with open(file_path, "rb") as f:
        files = {
            "files": ("audio_reference.mp3", f, "audio/mpeg")
        }
        print("Clonando a voz 'Cris Soberana Heritage' a partir da referência v13...")
        response = requests.post(url, headers=headers, data=data, files=files)

    if response.status_code == 200:
        res_json = response.json()
        voice_id = res_json.get("voice_id")
        print(f"SUCESSO! Novo ID da Voz Heritage: {voice_id}")
    else:
        print(f"Erro ao clonar voz (Status {response.status_code}): {response.text}")
except Exception as e:
    print(f"Exceção encontrada: {str(e)}")
