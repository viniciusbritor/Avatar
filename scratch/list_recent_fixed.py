import os
import base64
import sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Set stdout to UTF-8 to avoid encoding errors on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_recent_emails():
    token_path = r'c:\Users\vinic\workspace_antigravity\Avatar\token.json'
    if not os.path.exists(token_path):
        print(f"Token missing at {token_path}")
        return
    
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # List last 50 emails to be safe
    results = service.users().messages().list(userId='me', maxResults=50).execute()
    messages = results.get('messages', [])
    
    print(f"Searching in last {len(messages)} emails...\n")
    found_200 = False
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'No Date')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No Sender')
        snippet = msg['snippet']
        
        # Check for 200 or billing keywords
        if '200' in snippet or '200' in subject or any(kw in (subject + snippet).lower() for kw in ['cobrança', 'fatura', 'invoice', 'payment', 'billing', 'google cloud', 'cloud platform']):
            found_200 = True
            print(f"MATCH FOUND!")
            print(f"Date: {date}")
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print(f"Snippet: {snippet}")
            
            # Get content
            payload = msg['payload']
            parts = [payload]
            if 'parts' in payload:
                parts = payload['parts']
            
            body_text = ""
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
            
            if body_text:
                print(f"--- BODY START ---\n{body_text[:1000]}\n--- BODY END ---")
            print("-" * 60)
            
    if not found_200:
        print("No matches for '200' or billing keywords in the last 50 emails.")

if __name__ == "__main__":
    list_recent_emails()
