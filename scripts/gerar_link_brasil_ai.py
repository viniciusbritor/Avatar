import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import os
from google_auth_oauthlib.flow import Flow

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_FILE = os.path.join(ROOT_DIR, "client_secrets_master.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

OUTPUT_TOKEN = os.path.join(ROOT_DIR, "token_brasilia_youtube.json")

flow = Flow.from_client_secrets_file(
    SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri="http://localhost:8098"
)

auth_url, state = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    state="BRASIL_AI_CHANNEL"
)

print("\n" + "="*60)
print("LINK DE AUTORIZACAO - CANAL BRASIL AI (Apenas YouTube)")
print("="*60)
print("\nCopie e cole este link no navegador:")
print("\n" + auth_url)
print("\n" + "="*60)
print("INSTRUCOES:")
print("1. Selecione a conta de marca 'BrasilIIA' (Icone roxo B)")
print("2. Aceite as permissoes de YouTube")
print("3. Cole o URL do localhost aqui")
print("Token sera salvo em:", OUTPUT_TOKEN)
print("="*60 + "\n")
