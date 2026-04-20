import os
import base64
import sys
import io
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def find_charge_email():
    token_path = r'c:\Users\vinic\workspace_antigravity\Avatar\token.json'
    if not os.path.exists(token_path):
        print(f"Token missing at {token_path}")
        return
    
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # Search for Google Cloud billing emails specifically
    query = 'from:google-cloud-billing-noreply@google.com OR "fatura" OR "Google Cloud" OR "200"'
    results = service.users().messages().list(userId='me', q=query, maxResults=30).execute()
    messages = results.get('messages', [])
    
    print(f"Items found: {len(messages)}")
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
        from_val = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        snippet = msg['snippet']
        
        # If it has 200, or is billing
        if '200' in (subject + snippet) or 'fatura' in (subject + snippet).lower() or 'charge' in (subject + snippet).lower() or 'cobrança' in (subject + snippet).lower():
            print(f"--- MATCH ---")
            print(f"Date: {date}")
            print(f"From: {from_val}")
            print(f"Subject: {subject}")
            print(f"Snippet: {snippet}")
            
            # Extract content if it looks like a real charge
            if '200' in (subject + snippet):
                 payload = msg['payload']
                 body = ""
                 if 'parts' in payload:
                     for part in payload['parts']:
                         if part['mimeType'] == 'text/plain':
                             body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                             break
                 else:
                     body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
                 
                 print(f"FULL BODY SNIPPET:\n{body[:2000]}")
            print("-" * 60)

if __name__ == "__main__":
    find_charge_email()
