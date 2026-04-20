import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_FILE = os.path.join(ROOT_DIR, "client_secrets_master.json")
OUTPUT_TOKEN = os.path.join(ROOT_DIR, "token_brasilia_youtube.json")

with open(SECRETS_FILE, "r") as f:
    secrets = json.load(f)["installed"]

CLIENT_ID = secrets["client_id"]
CLIENT_SECRET = secrets["client_secret"]

# Gera link de autorização sem PKCE
import urllib.parse
SCOPES = " ".join([
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
])

auth_url = (
    "https://accounts.google.com/o/oauth2/auth"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri=http%3A%2F%2Flocalhost%3A8098"
    f"&scope={urllib.parse.quote(SCOPES, safe='').replace('%20', '+')}"
    f"&access_type=offline"
    f"&prompt=consent"
)

print("\n" + "="*60)
print("Acesse este link no navegador:")
print(auth_url)
print("="*60)
print("Selecione: BrasilIIA (YouTube) - icone roxo B")
print("Aguardando o retorno automatico...")

# Servidor que recebe o código
received_code = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            received_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Autorizado! Pode fechar esta aba.")
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # silencia logs

server = HTTPServer(("localhost", 8098), Handler)
server.timeout = 120
print("Aguardando autorizacao (ate 2 minutos)...")
server.handle_request()

if not received_code:
    print("Tempo esgotado. Tente novamente.")
    sys.exit(1)

print(f"\nCodigo recebido! Trocando por token...")

# Troca pelo token
response = requests.post("https://oauth2.googleapis.com/token", data={
    "code": received_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": "http://localhost:8098",
    "grant_type": "authorization_code"
})

token_data = response.json()

if "error" in token_data:
    print(f"Erro: {token_data}")
    sys.exit(1)

output = {
    "token": token_data["access_token"],
    "refresh_token": token_data.get("refresh_token"),
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scopes": token_data.get("scope", "").split(" ")
}

with open(OUTPUT_TOKEN, "w") as f:
    json.dump(output, f, indent=2)

print(f"Token salvo em: {OUTPUT_TOKEN}")

# Verificar canal
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
creds = Credentials.from_authorized_user_file(OUTPUT_TOKEN)
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
channels = youtube.channels().list(part="snippet", mine=True).execute()

if channels.get("items"):
    name = channels["items"][0]["snippet"]["title"]
    cid = channels["items"][0]["id"]
    print(f"\nCanal confirmado: {name}")
    print(f"ID do canal   : {cid}")
    if "brasil" in name.lower():
        print("\nESCUDO: Token VALIDO para o Brasil AI!")
        print("Pronto para iniciar os uploads oficiais.")
    else:
        print("ATENCAO: Canal errado -", name)
