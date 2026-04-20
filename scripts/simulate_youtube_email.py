import os
import json
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

TOKEN_FILE = "token_ultimate.json"

def send_simulation_email():
    if not os.path.exists(TOKEN_FILE):
        print("Erro: Token nao encontrado.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    service = build('gmail', 'v1', credentials=creds)
    
    # Cria a mensagem simulada
    msg = EmailMessage()
    msg.set_content("Hello! Your advanced features are now available on YouTube. You can now upload more videos daily.")
    msg['Subject'] = "Simulated: Advanced features are now available"
    msg['From'] = "viniciusbritor@gmail.com"
    msg['To'] = "viniciusbritor@gmail.com"
    
    # Codifica em base64
    encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    create_message = {'raw': encoded_message}
    
    # Envia
    try:
        service.users().messages().send(userId="me", body=create_message).execute()
        print("TESTE: E-mail de simulacao enviado com sucesso!")
        print("Agora aguarde ate 60 segundos para a Nuvem detectar e avisar seu computador.")
    except Exception as e:
        print(f"Erro ao enviar simulacao: {e}")

if __name__ == "__main__":
    send_simulation_email()
