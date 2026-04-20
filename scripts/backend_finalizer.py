import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Escopos Totais
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

def finalize_setup(auth_code):
    # 1. Troca o codigo pelo Token Ultimate
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8097'
    )
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"✅ Token Ultimate gerado.")

    # 2. Configura a Regra de Apps Script via Backend
    service = build('script', 'v1', credentials=creds)
    
    # Cria o projeto
    request = {'title': 'Brasil AI Cloud Watcher'}
    response = service.projects().create(body=request).execute()
    script_id = response['scriptId']
    print(f"✅ Projeto de Nuvem criado: {script_id}")

    # Conteudo do script
    file_content = {
        'files': [{
            'name': 'Code',
            'type': 'SERVER_JS',
            'source': """
function checkGmailAndTrigger() {
  var query = 'from:(google.com OR youtube.com) "recursos avançados" OR "advanced features"';
  var threads = GmailApp.search(query, 0, 1);
  if (threads.length > 0) {
    // Webhook receptor local (via Localtunnel)
    var url = 'https://brasil-ai-trigger.loca.lt/gmail-trigger';
    try {
      UrlFetchApp.fetch(url, {
        'method': 'post',
        'contentType': 'application/json',
        'payload': JSON.stringify({'status': 'approved'})
      });
    } catch(e) {}
  }
}
"""
        }, {
            'name': 'appsscript',
            'type': 'JSON',
            'source': '{"timeZone":"America/Sao_Paulo","exceptionLogging":"STACKDRIVER","runtimeVersion":"V8"}'
        }]
    }
    
    service.projects().updateContent(scriptId=script_id, body=file_content).execute()
    print(f"✅ Codigo enviado para a nuvem.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        finalize_setup(sys.argv[1])
