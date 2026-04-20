import requests
import json
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# CONFIGURACAO CORRETA COM ID LITERAL
PROJECT_ID = "brasili-ia-news"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/gmail-push-topic"
SUBSCRIPTION_NAME = f"projects/{PROJECT_ID}/subscriptions/gmail-push-sub"
WEBHOOK_URL = "https://brasil-ai-trigger.loca.lt/gmail-trigger"
TOKEN_FILE = "token_master_full.json"

def setup_instant_push_fix():
    if not os.path.exists(TOKEN_FILE):
        print("Erro: Token nao encontrado.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    
    # Ativa APIs
    pubsub = build('pubsub', 'v1', credentials=creds)
    gmail = build('gmail', 'v1', credentials=creds)

    # Cria Topico
    print(f"BACKEND: Criando topico no projeto {PROJECT_ID}...")
    try:
        pubsub.projects().topics().create(name=TOPIC_NAME, body={}).execute()
    except Exception as e:
        print(f"Nota: Topico ja existe ou ja esta ok.")

    # Permissão para o Gmail
    policy = {
        "policy": {
            "bindings": [{
                "role": "roles/pubsub.publisher",
                "members": ["serviceAccount:gmail-api-push@system.gserviceaccount.com"]
            }]
        }
    }
    pubsub.projects().topics().setIamPolicy(resource=TOPIC_NAME, body=policy).execute()

    # Cria Subscription de PUSH
    try:
        sub_body = {
            "topic": TOPIC_NAME,
            "pushConfig": {"pushEndpoint": WEBHOOK_URL}
        }
        pubsub.projects().subscriptions().create(name=SUBSCRIPTION_NAME, body=sub_body).execute()
        print(f"BACKEND: Inscricao Push roteada para {WEBHOOK_URL}")
    except Exception as e:
        print(f"Nota: Inscricao Push ja ativa.")

    # ATIVA O RELOGIO (ESTE EH O GATILHO)
    watch_request = {
        'topicName': TOPIC_NAME,
        'labelIds': ['INBOX']
    }
    gmail.users().watch(userId='me', body=watch_request).execute()
    print("--------------------------------------------------")
    print("SISTEMA DE GATILHO INSTANTANEO ON-LINE.")
    print("O Gmail agora avisa seu PC em tempo real.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    setup_instant_push_fix()
