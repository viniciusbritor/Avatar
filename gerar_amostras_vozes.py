import sys
import os
import requests

sys.path.append('C:/Users/vinic/workspace_antigravity/youtube')
import secrets_manager

def generate_sample(voice_id, name, text):
    api_key = secrets_manager.get_secret('ELEVEN_LABS_API_KEY')
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }
    
    output_path = f"amostra_{name}.mp3"
    print(f"Gerando amostra para: {name}...")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Salvo: {output_path}")
        else:
            print(f"❌ Erro em {name}: {response.text}")
    except Exception as e:
        print(f"⚠️ Erro de rede em {name}: {e}")

if __name__ == '__main__':
    frase_teste = "Atenção! Esta é uma demonstração exclusiva da minha voz para o canal Brasil EiAi. Como estou soando?"
    
    vozes_teste = [
        ("Larissa_Brasil_AI", "OjcGK1RXdMD1PFj2eIuN"),
        ("Mariana", "ZRrgtZQZxrh97Cig8y9w"),
        ("Mariana2", "H57lpZd9a8RhAccsai8Z"),
        ("Vivian", "Pmw4O6E456k07ZyjKQBK"),
        ("Sarah_Global", "EXAVITQu4vr4xnSDxMaL")
    ]
    
    print("Iniciando geração das amostras locais...\n")
    for name, v_id in vozes_teste:
        generate_sample(v_id, name, frase_teste)
    print("\nConcluído! Todos os arquivos MP3 de amostra estão na pasta raiz.")
