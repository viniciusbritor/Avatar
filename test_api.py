import requests
import google.auth.transport.requests
import google.oauth2.id_token

def test_avatar_generation():
    target_url = "https://avatar-efemero-180096224219.us-east4.run.app/generate"
    
    # Precisamos de um token de identidade para chamar o Cloud Run (--no-allow-unauthenticated)
    print("Obtendo token de identidade...")
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, target_url)
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    # Payload de teste
    # Nota: Assumindo que o arquivo lana_default.mp4 está no bucket brasil-ai-avatars
    payload = {
        "video_path": "gs://brasil-ai-avatars/lana_default.mp4",
        "audio_path": "gs://brasil-ai-avatars/test_audio.mp3", # Precisamos subir um teste!
        "output_path": "gs://brasil-ai-avatars/outputs/test_output.mp4"
    }
    
    print(f"Enviando requisição de teste para {target_url}...")
    try:
        response = requests.post(target_url, json=payload, headers=headers, timeout=600)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
    except Exception as e:
        print(f"Erro no teste: {str(e)}")

if __name__ == "__main__":
    test_avatar_generation()
