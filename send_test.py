import requests
res = requests.post("http://35.231.46.76:8080/produce", 
    headers={"X-API-Key": "brasilai-avatar-2026", "Content-Type": "application/json"},
    json={"text": "Olá sou a Cris. Esse é o teste 28!"})
print(res.status_code, res.text)
