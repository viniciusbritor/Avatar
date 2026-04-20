import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(ROOT_DIR, "token_brasilia_youtube.json")
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

VIDEO_ID = "a4BY7UH-HQg"

creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

try:
    youtube.videos().delete(id=VIDEO_ID).execute()
    print(f"Video {VIDEO_ID} excluido com sucesso!")
except Exception as e:
    print(f"Erro ao excluir: {e}")
