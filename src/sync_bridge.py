import os
import time
import json
from google.cloud import pubsub_v1
from google.cloud import storage

# --- CONFIGURAÇÕES INDUSTRIAIS ---
PROJECT_ID = "brasili-ia-news"
TOPIC_ID = "avatar-outputs-topic"
SUBSCRIPTION_ID = "avatar-local-sync-sub"
LOCAL_OUTPUT_DIR = r"c:\Users\vinic\workspace_antigravity\Avatar\sucesso"

def callback(message):
    """Processa a notificação do GCS e baixa o arquivo."""
    try:
        data = json.loads(message.data.decode("utf-8"))
        bucket_id = data.get("bucket")
        object_id = data.get("name")
        
        # Filtra para garantir que é um vídeo na pasta outputs
        if object_id.startswith("outputs/") and object_id.endswith(".mp4"):
            filename = os.path.basename(object_id)
            local_path = os.path.join(LOCAL_OUTPUT_DIR, filename)
            
            print(f"[BRIDGE] Novo vídeo detectado: {object_id}")
            print(f"[BRIDGE] Iniciando download instantâneo para {local_path}...")
            
            # Download via Storage SDK
            client = storage.Client(project=PROJECT_ID)
            bucket = client.bucket(bucket_id)
            blob = bucket.blob(object_id)
            blob.download_to_filename(local_path)
            
            print(f"[BRIDGE] SUCESSO: Vídeo entregue na máquina local.")
        
        message.ack() # Confirma o recebimento
    except Exception as e:
        print(f"[BRIDGE] ERRO ao processar mensagem: {e}")
        # Em caso de erro, não damos ACK para tentar novamente depois
        message.nack()

def start_bridge():
    """Inicia o listener do Pub/Sub."""
    if not os.path.exists(LOCAL_OUTPUT_DIR):
        os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    # Tenta criar a subscription se não existir
    try:
        topic_path = subscriber.topic_path(PROJECT_ID, TOPIC_ID)
        subscriber.create_subscription(name=subscription_path, topic=topic_path)
        print(f"[BRIDGE] Subscription criada: {SUBSCRIPTION_ID}")
    except Exception as e:
        if "AlreadyExists" in str(e):
            print(f"[BRIDGE] Reusando subscription existente: {SUBSCRIPTION_ID}")
        else:
            print(f"[BRIDGE] Erro ao criar subscription: {e}")

    print(f"[BRIDGE] Aguardando sinais do Maestro (Nuvem)...")
    
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    
    with subscriber:
        try:
            streaming_pull_future.result() # Fica rodando indefinidamente
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("[BRIDGE] Agente encerrado pelo usuário.")

if __name__ == "__main__":
    start_bridge()
