import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos Totais para Configuracao Backend
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/script.webapp.deploy",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"
TOKEN_FILE = "token_ultimate.json"

def generate_link():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8097'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n--- LINK DE AUTORIZACAO SUPREMA (BACKEND TOTAL) ---")
    print(auth_url)
    print("-" * 50)

if __name__ == "__main__":
    generate_link()
