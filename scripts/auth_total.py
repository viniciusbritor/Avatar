import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos Combinados: YouTube + Gmail
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/gmail.readonly"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"
TOKEN_FILE = "token_master_full.json"

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8096'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n--- LINK DE AUTORIZACAO TOTAL (YOUTUBE + GMAIL) ---")
    print(auth_url)
    print("-" * 50)
    
    code = input("\nCole o codigo de autorizacao TOTAL: ").strip()
    
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
        
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"\n✅ SUCESSO! Token TOTAL gerado em: {TOKEN_FILE}")

if __name__ == "__main__":
    get_credentials()
