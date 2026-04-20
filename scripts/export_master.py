import sqlite3
import json
import os

DB_PATH = "brasil_ai.db"

def export_master_secrets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM secrets WHERE key = 'YOUTUBE_CLIENT_ID'")
    client_id = cursor.fetchone()[1]
    
    cursor.execute("SELECT key, value FROM secrets WHERE key = 'YOUTUBE_CLIENT_SECRET'")
    client_secret = cursor.fetchone()[1]
    
    conn.close()
    
    # Monta o JSON padrão do Google OAuth
    master_json = {
        "installed": {
            "client_id": client_id,
            "project_id": "brasil-ai-full-master",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost:8095"]
        }
    }
    
    with open("client_secrets_master.json", "w") as f:
        json.dump(master_json, f, indent=2)
        
    print(f"✅ Arquivo client_secrets_master.json criado com as chaves do banco!")
    print(f"Client ID: {client_id}")

if __name__ == "__main__":
    export_master_secrets()
