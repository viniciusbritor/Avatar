import sys
import os

# Garantir que o script de voz está no path
sys.path.append('/workspace/skills/avatar_video_generation/scripts/')
try:
    from elevenlabs_tts import generate_tts
    
    text_path = '/workspace/input_text.txt'
    output_path = '/workspace/input_audio.mp3'
    
    if not os.path.exists(text_path):
        print(f"Erro: Arquivo {text_path} não encontrado.")
        sys.exit(1)
        
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
        
    print(f"🎙️ [ORQUESTRAÇÃO] Gerando áudio para: {text[:50]}...")
    success = generate_tts(text, output_path)
    
    if success:
        print("✅ [ORQUESTRAÇÃO] Áudio gerado com sucesso!")
    else:
        print("❌ [ORQUESTRAÇÃO] Falha na geração do áudio.")
        sys.exit(1)

except Exception as e:
    print(f"⚠️ [ERRO CRÍTICO] Falha no executor: {e}")
    sys.exit(1)
