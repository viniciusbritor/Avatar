import os
import json
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Escopos Supremos
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
    "https://www.googleapis.com/auth/script.webapp.deploy",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRETS_FILE = "client_secrets_master.json"
TOKEN_FILE = "token_ultimate.json"

def run_ultimate_loop():
    # 1. Inicia o Flow
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8097'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    
    print("\n" + "="*60)
    print("NOVO LINK DE AUTORIZACAO (LOOP FECHADO)")
    print("="*60)
    print(auth_url)
    print("="*60)
    
    code = input("\nCole a URL de retorno (ou apenas o codigo): ").strip()
    
    if "code=" in code:
        code = code.split("code=")[1].split("&")[0]
        
    # 2. Gera o Token
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print("\n✅ Token Gerado com Sucesso.")

    # 3. Configura o Backend na Nuvem
    print("📡 Configurando Regra de Vigilância na Nuvem...")
    service = build('script', 'v1', credentials=creds)
    
    request = {'title': 'Brasil AI Automator'}
    response = service.projects().create(body=request).execute()
    script_id = response['scriptId']
    
    file_content = {
        'files': [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': "function checkGmailAndTrigger() {\n  var query = 'from:(google.com OR youtube.com) \"recursos avançados\" OR \"advanced features\"';\n  var threads = GmailApp.search(query, 0, 1);\n  if (threads.length > 0) {\n    var url = 'https://brasil-ai-trigger.loca.lt/gmail-trigger';\n    try {\n      UrlFetchApp.fetch(url, {\n        'method': 'post',\n        'contentType': 'application/json',\n        'payload': JSON.stringify({'status': 'approved'})\n      });\n    } catch(e) {}\n  }\n}"
        }, {
            'name': 'appsscript',
            'type': 'JSON',
            'source': '{"timeZone":"America/Sao_Paulo","exceptionLogging":"STACKDRIVER","runtimeVersion":"V8"}'
        }]
    }
    
    service.projects().updateContent(scriptId=script_id, body=file_content).execute()
    print(f"✅ Regra de Nuvem configurada: {script_id}")
    print("\n--- TUDO PRONTO! O BACKEND ASSUMIU O CONTROLE ---")

if __name__ == "__main__":
    run_ultimate_loop()
