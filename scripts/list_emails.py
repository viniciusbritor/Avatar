import os
import sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Garante que o output seja UTF-8 no Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TOKEN_FILE = "token_master_full.json"

def list_recent_emails(limit=5):
    if not os.path.exists(TOKEN_FILE):
        print("Erro: Token não encontrado.")
        return
        
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build('gmail', 'v1', credentials=creds)
    
    results = service.users().messages().list(userId='me', maxResults=limit).execute()
    messages = results.get('messages', [])
    
    print(f"\n--- OS {limit} E-MAILS MAIS RECENTES ---")
    for msg in messages:
        detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = detail.get('snippet', '')
        # Extrai o REMETENTE dos headers
        headers = detail.get('payload', {}).get('headers', [])
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        print(f"\nDE: {sender}")
        print(f"DATA: {date}")
        print(f"RESUMO: {snippet[:120]}...")
        print("-" * 30)

if __name__ == "__main__":
    list_recent_emails()
