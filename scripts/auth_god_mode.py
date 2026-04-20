import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos Absolutos: YouTube + Gmail (Escrita/Envio) + Scripts + Drive
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"

def generate_god_mode_link():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8098'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n" + "="*60)
    print("LINK DE AUTORIZACAO TOTAL (GMAIL ESCRITA + TUDO)")
    print("="*60)
    print(auth_url)
    print("="*60)

if __name__ == "__main__":
    generate_god_mode_link()
