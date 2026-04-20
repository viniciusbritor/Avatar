import requests
import json
import os
import sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Garante UTF-8 no print
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TOKEN_FILE = "token_ultimate.json"

def complete_setup():
    if not os.path.exists(TOKEN_FILE):
        print("Erro: Token nao encontrado. O passo anterior falhou antes de salvar.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build('script', 'v1', credentials=creds)
    
    # 1. Cria o projeto
    print("BACKEND: Criando projeto no Google Apps Script...")
    project = service.projects().create(body={'title': 'Brasil AI Cloud Watcher Final'}).execute()
    script_id = project['scriptId']
    
    # 2. Pura o codigo de monitoramento
    print(f"BACKEND: Enviando codigo para o projeto {script_id}...")
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
    print("BACKEND: Codigo instalado com sucesso.")
    print("--------------------------------------------------")
    print("PROCESSO CONCLUIDO: A nuvem agora vigia seu Gmail.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    complete_setup()
