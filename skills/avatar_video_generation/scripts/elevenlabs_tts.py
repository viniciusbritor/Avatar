import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
import subprocess

# Injeta a pasta do secrets_manager no PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import secrets_manager

def generate_tts_microsoft_fallback(text, output_path):
    """Gera áudio via Microsoft (gratuito) usando PowerShell no Windows como fallback final."""
    print(f"🎙️ [FALLBACK] Usando voz Microsoft (Gratuito) para: {output_path}")
    # Nota: No Windows, usaremos a voz Francisca ou Maria via PowerShell que é excelente e free.
    ps_command = (
        f'Add-Type -AssemblyName System.Speech; '
        f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        f'$speak.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female, [System.Speech.Synthesis.VoiceAge]::Adult, 0, [System.Globalization.CultureInfo]::GetCultureInfo("pt-BR")); '
        f'$speak.SetOutputToWaveFile("{output_path.replace(".mp3", ".wav")}"); '
        f'$speak.Speak("{text}"); '
        f'$speak.Dispose();'
    )
    try:
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        # Converte WAV para MP3 se necessário (opcional, mantendo compatibilidade)
        if os.path.exists(output_path.replace(".mp3", ".wav")):
            # Se tiver ffmpeg, converte para manter o .mp3 esperado pelo pipeline
            cmd_conv = f'ffmpeg -y -i "{output_path.replace(".mp3", ".wav")}" -acodec libmp3lame "{output_path}"'
            subprocess.run(cmd_conv, shell=True, stderr=subprocess.DEVNULL)
            os.remove(output_path.replace(".mp3", ".wav"))
        print(f"✅ [FALLBACK] Áudio gerado via Microsoft com sucesso.")
        return True
    except Exception as e:
        print(f"❌ [FALLBACK ERROR] Falha total na geração de voz: {e}")
        return False

def generate_tts(text, output_path, voice_id="XrExE9yKIg1WjnnlVkGX", model_id="eleven_turbo_v2_5", voice_settings=None): # Sarah - Brasil AI (Oficial)
    """Gera áudio via ElevenLabs com fallback automático para Microsoft."""
    api_key = secrets_manager.get_secret("ELEVEN_LABS_API_KEY")
    if not api_key:
        print("⚠️ ELEVEN_LABS_API_KEY não encontrada. Indo para fallback.")
        return generate_tts_microsoft_fallback(text, output_path)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Configurações padrão ou personalizadas
    settings = voice_settings or {
        "stability": 0.50,
        "similarity_boost": 0.8,
        "style": 0.5,
        "use_speaker_boost": True
    }
    
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": settings
    }
    
    print(f"🎙️ [ELEVENLABS] Gerando áudio para: {output_path}")
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # Aceleração para fala mais humana e menos arrastada:
            fast_path = output_path.replace(".mp3", "_fast.mp3")
            subprocess.run(["ffmpeg", "-y", "-i", output_path, "-filter:a", "atempo=1.12", fast_path], capture_output=True)
            if os.path.exists(fast_path):
                os.replace(fast_path, output_path)

            print(f"✅ [ELEVENLABS] Áudio salvo e otimizado com sucesso: {output_path}")
            return True
        elif response.status_code == 401:
            print("❌ [ELEVENLABS] Créditos Excedidos ou Chave Inválida. Acionando Fallback Gratuito...")
            return generate_tts_microsoft_fallback(text, output_path)
        else:
            print(f"❌ [ELEVENLABS] Erro HTTP {response.status_code}: {response.text}. Acionando Fallback...")
            return generate_tts_microsoft_fallback(text, output_path)
    except Exception as e:
        print(f"⚠️ [ELEVENLABS] Erro de rede: {e}. Indo para Fallback.")
        return generate_tts_microsoft_fallback(text, output_path)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python elevenlabs_tts.py 'texto' 'caminho_saida'")
        sys.exit(1)
    generate_tts(sys.argv[1], sys.argv[2])
