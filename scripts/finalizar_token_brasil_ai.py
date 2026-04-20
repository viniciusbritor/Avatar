import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_FILE = os.path.join(ROOT_DIR, "client_secrets_master.json")
OUTPUT_TOKEN = os.path.join(ROOT_DIR, "token_brasilia_youtube.json")

CODE = "4/0Aci98E-gDM608hPPkrrvYnqNAw5Jpxo6Ifs-6-4LJccIuBGrYvqQU59cfQZKK8-H-bQ8Rg"

with open(SECRETS_FILE, "r") as f:
    secrets = json.load(f)["installed"]

CLIENT_ID = secrets["client_id"]
CLIENT_SECRET = secrets["client_secret"]

# Troca o code pelo token via HTTP direto (sem PKCE)
response = requests.post("https://oauth2.googleapis.com/token", data={
    "code": CODE,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": "http://localhost:8098",
    "grant_type": "authorization_code"
})

token_data = response.json()

if "error" in token_data:
    print(f"Erro ao obter token: {token_data}")
    sys.exit(1)

# Montar estrutura compatível com google.oauth2.credentials
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

# Verificar canal conectado
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
        print("ESCUDO: Token VALIDO para o Brasil AI. Pronto para upload!")
    else:
        print("ATENCAO: Canal errado -", name)
else:
    print("Nenhum canal encontrado.")
