import requests
import json
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Configurações
TOKEN_FILE = "token_master_full.json"
PROJECT_ID = "180096224219"
TOPIC_NAME = f"projects/{PROJECT_ID}/topics/gmail-push-topic"
SUBSCRIPTION_NAME = f"projects/{PROJECT_ID}/subscriptions/gmail-push-sub"
WEBHOOK_URL = "https://brasil-ai-trigger.loca.lt/gmail-trigger"
AUTH_CODE = "4/0Aci98E8SUEtRHiKpfCKhxf-TsmnqCerOmJHlj-IS-Xn5iBUjt3ELJk68uNu823FIS2ENCw"

# Carrega segredos do cliente
with open("client_secrets_master.json", "r") as f:
    client_data = json.load(f)["installed"]
    CLIENT_ID = client_data["client_id"]
    CLIENT_SECRET = client_data["client_secret"]

def setup_instant_push():
    # 1. Troca o codigo pelo Token PUSH
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": AUTH_CODE,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "http://localhost:8098",
        "grant_type": "authorization_code"
    }
    
    response = requests.post(url, data=data)
    token_res = response.json()
    
    if "access_token" not in token_res:
        print(f"Erro ao gerar token PUSH: {token_res}")
        return

    # Salva o token mestre definitivo com Cloud Perms
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
    print("BACKEND: Token de Elite instalado.")

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    
    # 2. Ativa Pub/Sub e Gmail Watch
    pubsub = build('pubsub', 'v1', credentials=creds)
    gmail = build('gmail', 'v1', credentials=creds)

    # Cria Topico
    try:
        pubsub.projects().topics().create(name=TOPIC_NAME, body={}).execute()
        print(f"BACKEND: Topico criado: {TOPIC_NAME}")
    except Exception as e:
        print(f"Topico ja existe ou erro: {e}")

    # Permissão para o Gmail no Topico
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
        print(f"BACKEND: Inscricao Push ativada para {WEBHOOK_URL}")
    except Exception as e:
        print(f"Inscricao ja existe ou erro: {e}")

    # 3. ATIVA O RELOGIO (GMAIL WATCH)
    watch_request = {
        'topicName': TOPIC_NAME,
        'labelIds': ['INBOX']
    }
    gmail.users().watch(userId='me', body=watch_request).execute()
    print("🚀 GATILHO INSTANTANEO ATIVADO! O Gmail agora empurra o sinal para o seu PC.")

if __name__ == "__main__":
    setup_instant_push()
