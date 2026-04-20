import sys
import os
import requests

# Ajuste do path para importar module local
sys.path.append('C:/Users/vinic/workspace_antigravity/youtube')
import secrets_manager

def list_voices():
    api_key = secrets_manager.get_secret('ELEVEN_LABS_API_KEY')
    url = 'https://api.elevenlabs.io/v1/voices'
    headers = {'xi-api-key': api_key}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        artifact_path = 'vozes_elevenlabs.md'
        with open(artifact_path, 'w', encoding='utf-8') as f:
            f.write('# 🎙️ Catálogo de Vozes - ElevenLabs\n\n')
            f.write('| Nome | ID | Tipo | Gênero | Sotaque | Tema |\n')
            f.write('|---|---|---|---|---|---|\n')
            for v in data.get('voices', []):
                labels = v.get('labels', {})
                accent = labels.get('accent', 'N/A')
                gender = labels.get('gender', 'N/A')
                use_case = labels.get('use case', 'N/A')
                category = v.get('category', 'N/A')
                
                f.write(f"| **{v['name']}** | `{v['voice_id']}` | {category} | {gender} | {accent} | {use_case} |\n")
        print(f"Catalogo salvo com sucesso em {artifact_path}")
    else:
        print('Erro na API:', response.text)

if __name__ == '__main__':
    list_voices()
