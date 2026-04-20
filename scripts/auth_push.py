import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos de Elite: Cloud Platform + PubSub + Gmail + YouTube
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"

def generate_push_link():
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8098'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n" + "="*60)
    print("LINK GATILHO INSTANTANEO (PUSH)")
    print("="*60)
    print(auth_url)
    print("="*60)

if __name__ == "__main__":
    generate_push_link()
