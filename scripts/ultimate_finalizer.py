import requests
import json
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Carrega segredos do cliente
with open("client_secrets_master.json", "r") as f:
    client_data = json.load(f)["installed"]
    CLIENT_ID = client_data["client_id"]
    CLIENT_SECRET = client_data["client_secret"]

REDIRECT_URI = "http://localhost:8097"
AUTH_CODE = "4/0Aci98E8Pv_Aia-CTwZYDImblKshqPut-4fp9KZH6he74Kgj4Fv5b-ZOrfoO6ujU_Yy8M1g"
TOKEN_FILE = "token_ultimate.json"

def finalize_backend():
    # 1. Troca o codigo pelo Token
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
        print(f"Erro ao gerar token: {token_res}")
        return

    # Salva o token ultimate
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
    print("✅ Token Ultimate salvo no backend.")

    # 2. Configura Apps Script via API
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build('script', 'v1', credentials=creds)
    
    project = service.projects().create(body={'title': 'Brasil AI Cloud Watcher v2'}).execute()
    script_id = project['scriptId']
    
    content = {
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
    
    service.projects().updateContent(scriptId=script_id, body=content).execute()
    print(f"✅ Regra de Nuvem instalada com sucesso! Script ID: {script_id}")
    print("\n🚀 CONFIGURACAO COMPLETA. O sistema agora e reativo ao seu Gmail.")

if __name__ == "__main__":
    finalize_backend()
