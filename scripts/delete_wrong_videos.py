import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import googleapiclient.discovery
from google.oauth2.credentials import Credentials

TOKEN_FILE = "token_master_full.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload"
]

def delete_videos():
    if not os.path.exists(TOKEN_FILE):
        print("Token nao encontrado.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    folders = ["p_6472", "p_6513", "p_6475", "p_6512"]
    
    for folder in folders:
        manifest_path = f"workspace_brasil_ia/{folder}/09_upload_manifest.json"
        
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            video_id = manifest.get("video_id")
            
            if video_id:
                try:
                    print(f"🗑️ Deletando vídeo {video_id} da conta atual...")
                    youtube.videos().delete(id=video_id).execute()
                    print(f"✅ Vídeo {video_id} excluído com sucesso do canal!")
                except Exception as e:
                    print(f"⚠️ Erro ao excluir {video_id}: {e}")
            
            # Remove o manifest para forçar re-upload no futuro
            os.remove(manifest_path)
            print(f"🧹 Manifest {manifest_path} removido para permitir re-upload.")
        else:
            print(f"Ignorando {folder}, manifest não encontrado.")

if __name__ == "__main__":
    delete_videos()
