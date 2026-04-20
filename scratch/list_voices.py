import requests

keys = [
    "sk_9c814121f81889cfd0ff4e776a846d9561b1936515fc1901",
    "sk_65c08421d3c03d45e0c08df024705c0c604532b49b142c48"
]

for k in keys:
    print(f"\n--- Account: {k[:8]}... ---")
    r = requests.get('https://api.elevenlabs.io/v1/voices', headers={'xi-api-key': k})
    if r.status_code == 200:
        voices = r.json().get('voices', [])
        for v in voices:
            print(f"Name: {v['name']}, ID: {v['voice_id']}, Category: {v['category']}")
    else:
        print(f"Error ({r.status_code}): {r.text}")
