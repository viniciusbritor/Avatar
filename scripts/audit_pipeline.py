import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os, json, sqlite3

print('=== TOKENS ===')
for t in ['token_brasilia_youtube.json','token_master_full.json','token.json','client_secrets_master.json']:
    p = os.path.join('.', t)
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        rt = bool(d.get('refresh_token'))
        print(f'  {t}: OK (refresh={rt})')
    else:
        print(f'  {t}: AUSENTE')

print()
print('=== BANCO SQL ===')
if os.path.exists('brasil_ai.db'):
    conn = sqlite3.connect('brasil_ai.db')
    c = conn.cursor()
    c.execute('SELECT count(*) FROM pautas')
    total = c.fetchone()[0]
    c.execute("SELECT status, count(*) FROM pautas GROUP BY status")
    stats = c.fetchall()
    conn.close()
    print(f'  Total pautas: {total}')
    for s, cnt in stats:
        print(f'    {s}: {cnt}')
else:
    print('  brasil_ai.db: AUSENTE')

print()
print('=== SKILLS (scripts referenciados) ===')
skills = [
    ('News Hunter', 'skills/news_hunter/scripts/news_hunter_live.py'),
    ('Video Downloader', 'skills/video_downloader/scripts/download_news.py'),
    ('Smart Clipper', 'skills/video_cutter_engine/scripts/news_clipper_master.py'),
    ('Script Generator', 'skills/script_generator/scripts/cris_script_master.py'),
    ('ElevenLabs TTS', 'skills/avatar_video_generation/scripts/elevenlabs_tts.py'),
    ('D-ID Avatar', 'skills/avatar_video_generation/scripts/generate_did_video.py'),
    ('Thumbnail Generator', 'skills/branding_high_end/scripts/generate_thumbnail_journalistic.py'),
    ('Copyright Shield', 'skills/copyright_shield/scripts/apply_shield.py'),
    ('Video Assembler', 'skills/video_cutter_engine/scripts/video_assembler_v2.py'),
    ('Branding Guardian', 'skills/branding_high_end/scripts/branding_alignment_guardian.py'),
    ('Upload Master', 'skills/youtube_uploader/scripts/upload_master_v2.py'),
    ('Retry Thumbnails', 'skills/youtube_uploader/scripts/retry_failed_thumbnails.py'),
    ('System Guardian', 'skills/system_guardian/scripts/active_guardian.py'),
]
for name, path in skills:
    exists = os.path.exists(path)
    print(f'  {name}: {"OK" if exists else "AUSENTE"} ({path})')

print()
print('=== APIs EXTERNAS (env vars) ===')
env_keys = ['ELEVENLABS_API_KEY', 'DID_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_API_KEY', 'FAL_KEY']
for k in env_keys:
    val = os.environ.get(k)
    if val:
        print(f'  {k}: OK ({val[:8]}...)')
    else:
        print(f'  {k}: NAO CONFIGURADA')

print()
print('=== FFMPEG ===')
ffmpeg_ok = os.system('ffmpeg -version > nul 2>&1') == 0
print(f'  ffmpeg: {"OK" if ffmpeg_ok else "AUSENTE"}')
