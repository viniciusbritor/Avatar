import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def check_quotas():
    if not os.path.exists('token.json'):
        print("Token missing")
        return
    
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('gmail', 'v1', credentials=creds)
    
    # Search for quota related emails
    results = service.users().messages().list(userId='me', q='quota', maxResults=5).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No quota emails found.")
        return
        
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id']).execute()
        subject = next((h['value'] for h in msg['payload']['headers'] if h['name'].lower() == 'subject'), 'No Subject')
        date = next((h['value'] for h in msg['payload']['headers'] if h['name'].lower() == 'date'), 'No Date')
        print(f"ID: {m['id']}")
        print(f"Date: {date}")
        print(f"Subject: {subject}")
        print(f"Snippet: {msg['snippet']}")
        print("-" * 40)

if __name__ == "__main__":
    check_quotas()
