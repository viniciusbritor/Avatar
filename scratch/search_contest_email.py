import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return build('gmail', 'v1', credentials=creds)
    return None

def search_email():
    try:
        service = get_gmail_service()
        if not service:
            print("Token not found.")
            return

        # Busca pelo ID do caso 70155577
        query = '70155577'
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print('Nenhum e-mail encontrado com o ID do caso 70155577.')
            return

        print(f"Encontrado(s) {len(messages)} e-mail(s):\n")
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            print(f"ID: {m['id']}")
            print(f"Resumo: {msg['snippet']}")
            print("-" * 30)
        
    except Exception as e:
        print(f'Erro: {str(e)}')

if __name__ == "__main__":
    search_email()
