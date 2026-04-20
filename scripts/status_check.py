import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os, json

print('=== MANIFESTOS DE UPLOAD ===')
for folder in sorted(os.listdir('workspace_brasil_ia')):
    m = os.path.join('workspace_brasil_ia', folder, '09_upload_manifest.json')
    vid5 = os.path.join('workspace_brasil_ia', folder, '05_REPRODUCAO_CORRETA_YOUTUBE.mp4')
    if os.path.exists(m):
        with open(m, 'r', encoding='utf-8') as f:
            d = json.load(f)
        vid_id = d.get('video_id', 'N/A')
        thumb = d.get('thumbnail_status', 'sem_registro')
        url = d.get('youtube_url', '')
        print(f"  {folder}: {vid_id} | thumb={thumb} | {url}")
    elif os.path.exists(vid5):
        print(f"  {folder}: PRONTO PARA UPLOAD (sem manifest)")
