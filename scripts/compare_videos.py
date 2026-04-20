import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import re
import os

files = {
    'a4BY7UH-HQg': r'C:\Users\vinic\.gemini\antigravity\brain\3b184a50-0f63-4af9-bc05-5f3b117b8162\.system_generated\steps\1653\content.md',
    'LXIKBmvss7E': r'C:\Users\vinic\.gemini\antigravity\brain\3b184a50-0f63-4af9-bc05-5f3b117b8162\.system_generated\steps\1654\content.md',
}

for vid, path in files.items():
    if not os.path.exists(path):
        print(f"Arquivo nao encontrado: {path}")
        continue
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Duracao em ISO 8601 (PT#M#S)
    dur = re.findall(r'"duration":"(PT[^"]+)"', content)
    view = re.findall(r'"viewCount"[^"]*"(\d+)"', content)
    upload = re.findall(r'"uploadDate":"([^"]+)"', content)
    likes = re.findall(r'"likeCount"[^"]*"(\d+)"', content)
    channel = re.findall(r'"ownerChannelName":"([^"]+)"', content)
    
    print(f"\n=== VIDEO {vid} ===")
    print(f"Duracao   : {dur[0] if dur else 'N/A'}")
    print(f"Views     : {view[0] if view else 'N/A'}")
    print(f"Likes     : {likes[0] if likes else 'N/A'}")
    print(f"Upload    : {upload[0] if upload else 'N/A'}")
    print(f"Canal     : {channel[0] if channel else 'N/A'}")
