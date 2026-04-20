import os
import base64
import sys
import io
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def find_charge_email():
    token_path = r'c:\Users\vinic\workspace_antigravity\Avatar\token.json'
    if not os.path.exists(token_path):
        return
    
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # Search for "200" and "cobrança" or "fatura"
    query = '200 (cobrança OR fatura OR invoice OR "Google Cloud")'
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])
    
    with open('charge_result.txt', 'w', encoding='utf-8') as f:
        for m in messages:
            msg = service.users().messages().get(userId='me', id=m['id']).execute()
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            from_val = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            snippet = msg['snippet']
            
            f.write(f"ID: {m['id']}\n")
            f.write(f"Date: {date}\n")
            f.write(f"From: {from_val}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Snippet: {snippet}\n")
            
            payload = msg['payload']
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
            else:
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            
            f.write(f"BODY:\n{body}\n")
            f.write("-" * 80 + "\n")

if __name__ == "__main__":
    find_charge_email()
