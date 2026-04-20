import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"
TOKEN_FILE = "token_master.json"

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8095'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n--- LINK DE AUTORIZACAO MASTER ---")
    print(auth_url)
    print("-" * 50)
    
    code = input("\nCole o codigo de autorizacao Master: ").strip()
    
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
        
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"\nSucesso! Token MASTER gerado em: {TOKEN_FILE}")

if __name__ == "__main__":
    get_credentials()
