import requests, time, sys
ip = "34.186.50.105"
for i in range(30):
    try:
        r = requests.get(f"http://{ip}:8080/health", timeout=5)
        print(f"[{time.strftime('%X')}] /health OK: {r.status_code} -> {r.text}")
        sys.exit(0)
    except Exception as e:
        print(f"[{time.strftime('%X')}] aguardando... ({i*5}s)")
        time.sleep(5)
print("TIMEOUT: API nao respondeu em 150s")
