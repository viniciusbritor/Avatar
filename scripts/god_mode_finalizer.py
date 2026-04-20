import requests
import json
import os
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Carrega segredos do cliente
with open("client_secrets_master.json", "r") as f:
    client_data = json.load(f)["installed"]
    CLIENT_ID = client_data["client_id"]
    CLIENT_SECRET = client_data["client_secret"]

REDIRECT_URI = "http://localhost:8098"
AUTH_CODE = "4/0Aci98E-vDK-oMXNssbfQShqiNrk2n0TRQTK3EFOC_JRGWOQ9CHQacYrPmORcLmIxVR08hw"
TOKEN_FILE = "token_master_full.json"

def upgrade_to_god_mode():
    # 1. Troca o codigo pelo Token de Escrita
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": AUTH_CODE,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(url, data=data)
    token_res = response.json()
    
    if "access_token" not in token_res:
        print(f"Erro ao gerar token God Mode: {token_res}")
        return

    # Salva o token mestre definitivo
    creds_data = {
        "token": token_res["access_token"],
        "refresh_token": token_res.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scopes": token_res.get("scope", "").split(" ")
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(creds_data, f)
    print("BACKEND: Token God Mode instalado.")

    # 2. TESTE REAL: Enviar o e-mail de simulacao
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build('gmail', 'v1', credentials=creds)
    
    msg = EmailMessage()
    msg.set_content("Simulacao: Seus recursos avancados do YouTube estao ativos!")
    msg['Subject'] = "Advanced features are now available (Test Run)"
    msg['From'] = "viniciusbritor@gmail.com"
    msg['To'] = "viniciusbritor@gmail.com"
    
    encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={'raw': encoded_message}).execute()
    print("BACKEND: E-mail de teste enviado com sucesso via API de Escrita!")

if __name__ == "__main__":
    upgrade_to_god_mode()
