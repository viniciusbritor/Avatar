import requests
import json
import time
import base64
import os
import subprocess
import sys

# Fix: força UTF-8 no stdout para evitar UnicodeEncodeError com emojis no Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Adiciona o root do projeto ao path para importar o secrets_manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../../..")
from secrets_manager import get_secret

# --- CREDENCIAIS — carregadas do banco (brasil_ai.db) em tempo de execução ---
API_KEY = get_secret("DID_BASIC_AUTH")
if not API_KEY:
    raise ValueError("❌ [FATAL] A chave 'DID_BASIC_AUTH' não foi encontrada no banco SQLite do secrets_manager.")

PRESENTER_ID = get_secret("DID_PRESENTER_ID") or "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"

# v18.2.0: Substitui a string fixa para receber o workspace_path do LangGraph
WORKSPACE = os.path.abspath(sys.argv[-1]) if len(sys.argv) > 1 else os.path.abspath("workspace_brasil_ia")


def normalize_avatar_to_master_spec(avatar_path):
    """v19.1.0: Unificação Proporcional Brasil-AI — 720p 16:9 Nativo (Wide)."""
    print(f"⚖️ Normalizando em 720p Wide: {os.path.basename(avatar_path)}...")
    temp_path = avatar_path.replace(".mp4", "_raw.mp4")
    os.rename(avatar_path, temp_path)
    norm_cmd = (
        f'ffmpeg -y -i "{temp_path}" -vf '
        # v21.1.0: Preserva aspecto 1:1 nativo do D-ID (1080x1080) e apenas escala a altura para encaixar na tela se necessário
        f'"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30" '
        f'-c:v libx264 -preset fast -crf 20 -c:a aac -ar 44100 "{avatar_path}"'
    )
    subprocess.run(norm_cmd, shell=True, stderr=subprocess.DEVNULL)
    if os.path.exists(temp_path):
        os.remove(temp_path)


def generate_did_video(text, filename="avatar_test.mp4", presenter_id=None, audio_path=None):
    use_id = presenter_id if presenter_id else PRESENTER_ID
    print(f"🎬 Solicitando Clipe D-ID ({use_id}): {filename}...")
    url = "https://api.d-id.com/clips"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "presenter_id": use_id
    }

    if audio_path and os.path.exists(audio_path):
        print(f"   🎙️ [VOZ] Usando áudio externo auditado: {os.path.basename(audio_path)}")
        # 1. Upload do Áudio para o D-ID para obter a URL temporária
        upload_url = "https://api.d-id.com/audios"
        audio_headers = {"Authorization": f"Basic {API_KEY}"}
        with open(audio_path, "rb") as audio_file:
            files = {"audio": audio_file}
            r_upload = requests.post(upload_url, headers=audio_headers, files=files)
            if r_upload.status_code != 201:
                print(f"❌ [ERROR] Upload áudio falhou: {r_upload.text}")
                return None
            audio_url = r_upload.json().get("url")
            payload["script"] = {"type": "audio", "audio_url": audio_url}
    else:
        # Fallback para texto — FORÇANDO VOZ pt-BR PARA EVITAR INGLÊS
        print("   🎙️ [VOZ] Fallback: Microsoft pt-BR-FranciscaNeural (Voz Oficial)")
        voice_provider = {"type": "microsoft", "voice_id": "pt-BR-FranciscaNeural"}
        payload["script"] = {
            "type": "text",
            "input": text,
            "provider": voice_provider
        }

    res = requests.post(url, headers=headers, json=payload, timeout=60)
    if res.status_code != 201:
        print(f"❌ [ERROR] D-ID {res.status_code}: {res.text}")
        return None

    clip_id = res.json().get("id")
    print(f"⏳ Renderizando... ID: {clip_id}")

    for attempt in range(100):
        time.sleep(5)
        try:
            poll = requests.get(f"{url}/{clip_id}", headers=headers, timeout=15)
            data = poll.json()
            status = data.get("status")

            if status == "done":
                v_res = requests.get(data["result_url"], timeout=30)
                target_path = os.path.join(WORKSPACE, filename)
                os.makedirs(WORKSPACE, exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(v_res.content)
                normalize_avatar_to_master_spec(target_path)
                print(f"✅ Avatar salvo: {target_path}")
                return target_path
            elif status == "error":
                print(f"❌ Erro D-ID: {data.get('error')}")
                return None
            elif attempt >= 99:
                print(f"🛑 [WATCHDOG] O D-ID ultrapassou o limite de 500 segundos. Abortando tentativa.")
                return None
            elif attempt % 10 == 0:
                print(f"   ⏳ Aguardando... {attempt+1}/100")
        except Exception as e:
            print(f"⚠️ {e}")
            if attempt > 10: return None # Fail fast on connection errors

    print("❌ Tempo limite excedido.")
    return None


def run_avatar_production():
    script_file = os.path.join(WORKSPACE, "04_roteiro_fonetico.json")
    with open(script_file, "r", encoding="utf-8") as f:
        script = json.load(f)

    # Clip 1: Intro
    generate_did_video(script["intro_cris_video"], "05_cris_intro.mp4",
                       audio_path=os.path.join(WORKSPACE, "intro_audio.mp3"))

    # Clip 2: Comentario — SOMENTE se comentario_audio.mp3 existir (modo PREMIUM)
    # No modo ECONOMICO o audio nao e gerado separado, entao pulamos este clip
    comentario_audio = os.path.join(WORKSPACE, "comentario_audio.mp3")
    comentario_text = script.get("comentario_cris_video", "").strip()
    if os.path.exists(comentario_audio) and comentario_text:
        generate_did_video(comentario_text, "05_cris_comentario.mp4",
                           audio_path=comentario_audio)
    else:
        print("   💰 [ESTRUTURA LEAN] Pulando clip de comentario (texto vazio ou audio ausente).")

    # Clip 3: Outro
    generate_did_video(script["conclusion_cris_video"], "05_cris_outro.mp4",
                       audio_path=os.path.join(WORKSPACE, "outro_audio.mp3"))



if __name__ == "__main__":
    run_avatar_production()
