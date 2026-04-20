import requests
import json
import time
import base64
import os
import subprocess

# Credenciais
RAW_KEY = "dmluaWNpdXNicml0b3JAZ21haWwuY29t:jYq4FSnw268wbz_X7FZ8z"
API_KEY = base64.b64encode(RAW_KEY.encode()).decode()
PRESENTER_ID = "v2_public_lana_black_suite_green_screen@BTQAFVuIxZ"

WORKSPACE = "workspace_demos"

DEMOS = [
    {
        "id": "demo_economia",
        "script": "Olá! Seja bem-vindo ao Brasil IA. Hoje o mercado reagiu positivamente às novas projeções econômicas, com o IBOVESPA atingindo patamares históricos. Vamos conferir os detalhes desse cenário que impacta o bolso de todos os brasileiros.",
        "filename": "01_demo_economia_raw.mp4"
    },
    {
        "id": "demo_politica",
        "script": "Boa noite. No cenário político de Brasília, as atenções se voltam para a votação da nova reforma tributária. O governo busca apoio decisivo no Congresso enquanto a oposição articula mudanças no texto base. Acompanhe a nossa análise completa.",
        "filename": "02_demo_politica_raw.mp4"
    },
    {
        "id": "demo_stf",
        "script": "O Supremo Tribunal Federal retomou hoje o julgamento sobre o marco temporal. O voto da relatora trouxe novas perspectivas para a segurança jurídica no país. Fique por dentro de todos os desdobramentos desta decisão histórica aqui no Brasil IA.",
        "filename": "03_demo_stf_raw.mp4"
    },
    {
        "id": "demo_mundo",
        "script": "No cenário internacional, as tensões geopolíticas no Oriente Médio continuam a preocupar líderes globais. O barril do petróleo sofreu oscilações significativas após os últimos eventos diplomáticos. Vamos entender como isso afeta a economia global.",
        "filename": "04_demo_mundo_raw.mp4"
    }
]

def generate_did_video(text, filename):
    url = "https://api.d-id.com/clips"
    headers = {
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "pt-BR-FranciscaNeural"}
        },
        "presenter_id": PRESENTER_ID
    }
    
    print(f"🎬 Solicitando D-ID ({filename})...")
    res = requests.post(url, headers=headers, json=payload, timeout=60)
    if res.status_code != 201:
        print(f"❌ Erro API: {res.status_code} - {res.text}")
        return None
        
    clip_id = res.json()['id']
    while True:
        time.sleep(5)
        res_poll = requests.get(f"{url}/{clip_id}", headers=headers, timeout=15)
        data = res_poll.json()
        if data.get('status') == 'done':
            video_url = data['result_url']
            v_res = requests.get(video_url, timeout=30)
            target_path = os.path.join(WORKSPACE, filename)
            with open(target_path, 'wb') as f:
                f.write(v_res.content)
            return target_path
        elif data.get('status') == 'error':
            print(f"❌ Erro D-ID processamento.")
            return None

def process_with_background(input_vid, output_name):
    print(f"🎞️ Aplicando fundo de newsroom: {output_name}")
    editor_script = "c:/Users/vinic/workspace_antigravity/youtube/skills/video_cutter_engine/scripts/brasil_ia_editor_newsroom.py"
    # Modificamos o script de editor para aceitar argumentos ou apenas rodamos o comando FFmpeg diretamente aqui
    bg_img = "c:/Users/vinic/workspace_antigravity/youtube/fundo_telejornal.png"
    
    filter_str = (
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p[bg]; "
        "[1:v]chromakey=0x00AD3D:0.35:0.1,scale=1920:1080,format=yuva420p[ava]; "
        "[bg][ava]overlay=0:0,format=yuv420p[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "5", # Duração será ajustada via ffprobe no script original mas aqui simplificamos para o demo
        "-i", bg_img,
        "-i", input_vid,
        "-filter_complex", filter_str,
        "-map", "[out]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_name
    ]
    
    subprocess.run(cmd, stderr=subprocess.DEVNULL)
    print(f"✅ Demo Final: {output_name}")

def run_demos():
    if not os.path.exists(WORKSPACE):
        os.makedirs(WORKSPACE)
    
    for demo in DEMOS:
        raw_vid = generate_did_video(demo["script"], demo["filename"])
        if raw_vid:
            final_name = os.path.join(WORKSPACE, f"{demo['id']}_final_newsroom.mp4")
            process_with_background(raw_vid, final_name)

if __name__ == "__main__":
    run_demos()
