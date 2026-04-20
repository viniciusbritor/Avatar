import requests
import os
import sys

# Adiciona o root do projeto ao path para importar o secrets_manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secrets_manager import get_secret

def check_did_credits():
    api_key = get_secret("DID_BASIC_AUTH")
    if not api_key:
        print("❌ Chave DID_BASIC_AUTH nao encontrada.")
        return

    url = "https://api.d-id.com/credits"
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            remaining = data.get("remaining", "N/A")
            total = data.get("total", "N/A")
            print(f"📊 [D-ID CREDITS] Restantes: {remaining} | Total: {total}")
        else:
            print(f"❌ Erro ao consultar D-ID: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Falha na conexao: {e}")

if __name__ == "__main__":
    check_did_credits()
