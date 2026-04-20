import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def list_recent_emails():
    token_path = r'c:\Users\vinic\workspace_antigravity\Avatar\token.json'
    if not os.path.exists(token_path):
        print(f"Token missing at {token_path}")
        return
    
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # List last 20 emails
    results = service.users().messages().list(userId='me', maxResults=20).execute()
    messages = results.get('messages', [])
    
    print(f"Listing last {len(messages)} emails:\n")
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'No Date')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No Sender')
        print(f"Date: {date} | From: {sender} | Subject: {subject} | Snippet: {msg['snippet'][:100]}")
        print("-" * 20)

if __name__ == "__main__":
    list_recent_emails()
