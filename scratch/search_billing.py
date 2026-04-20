import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def search_billing():
    token_path = r'c:\Users\vinic\workspace_antigravity\Avatar\token.json'
    if not os.path.exists(token_path):
        print(f"Token missing at {token_path}")
        return
    
    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)
    
    # Search for billing related emails with "200"
    query = '200 (cobrança OR fatura OR invoice OR "Google Cloud" OR payment)'
    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No matches found for query: " + query)
        # Try a broader search if no results
        results = service.users().messages().list(userId='me', q='200', maxResults=10).execute()
        messages = results.get('messages', [])
        
    if not messages:
        print("No emails with '200' found.")
        return
        
    print(f"Found {len(messages)} matching emails.\n")
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'No Date')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'No Sender')
        
        print(f"ID: {m['id']}")
        print(f"Date: {date}")
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Snippet: {msg['snippet']}")
        
        # Get content
        payload = msg['payload']
        parts = payload.get('parts', [])
        body = ""
        if not parts:
            body = payload.get('body', {}).get('data', "")
        else:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body = part.get('body', {}).get('data', "")
                    break
        
        if body:
            try:
                text = base64.urlsafe_b64decode(body).decode('utf-8')
                print(f"Content Summary: {text[:500]}...")
            except:
                print("Could not decode content.")
        
        print("-" * 60)

if __name__ == "__main__":
    search_billing()
