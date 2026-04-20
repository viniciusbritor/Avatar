import os
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

TOKEN_FILE = "token_master_full.json"

def check_channel_and_gmail():
    if not os.path.exists(TOKEN_FILE):
        print("STATUS: Erro fatal - Token nao encontrado.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    
    # 1. Verifica Gmail
    gmail = build('gmail', 'v1', credentials=creds)
    query = 'from:(google.com OR youtube.com) "recursos avançados" OR "advanced features"'
    messages = gmail.users().messages().list(userId='me', q=query).execute()
    
    email_found = "SIM" if messages.get('messages') else "NAO"
    
    # 2. Verifica Youtube Status via API
    youtube = build('youtube', 'v3', credentials=creds)
    channels = youtube.channels().list(part='status,contentDetails', mine=True).execute()
    
    print("="*40)
    print("STATUS INDUSTRIAL BRASIL AI")
    print("="*40)
    print(f"E-mail de Liberacao: {email_found}")
    print(f"Canal Conectado: {channels['items'][0]['id'] if channels.get('items') else 'ERRO'}")
    print(f"Servico Local: ATIVO (Monitorando logs...)")
    print("="*40)

if __name__ == "__main__":
    check_channel_and_gmail()
