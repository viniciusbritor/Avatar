import requests
import json
import os

PROJECT_ID = "brasili-ia-news"
TOKEN_FILE = "token_master_full.json"

# Carrega segredos do cliente
with open("client_secrets_master.json", "r") as f:
    client_data = json.load(f)["installed"]
    CLIENT_ID = client_data["client_id"]
    CLIENT_SECRET = client_data["client_secret"]

def finalize_ultimate_sync(code):
    url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "http://localhost:8098",
        "grant_type": "authorization_code"
    }
    
    response = requests.post(url, data=data)
    token_res = response.json()
    
    if "access_token" not in token_res:
        print(f"Erro: {token_res}")
        return

    # Salva o UNICO token com todos os escopos
    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "token": token_res["access_token"],
            "refresh_token": token_res.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": token_res.get("scope", "").split(" ")
        }, f)
    print("BACKEND: Sincronizacao Total Concluida. Status: OVERLORD.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        finalize_ultimate_sync(sys.argv[1])
