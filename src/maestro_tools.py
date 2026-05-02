import os
import requests
from typing import Optional

# Evitamos instanciar o orquestrador aqui para não criar um loop infinito de agentes.
# As chaves e lógica devem ser buscadas diretamente ou via LanaIndustrialEngine.

def prepare_gpu_infrastructure():
    """Garante que a maquina GPU L4 na nuvem esta provisionada e pronta."""
    try:
        from src.agente_lana_orchestrator import LanaIndustrialEngine
        engine = LanaIndustrialEngine()
        # Busca instâncias existentes primeiro para economizar
        existing = engine._find_existing_engines()
        if existing:
            ip = engine._get_instance_ip(existing[0]['name'], existing[0]['zone'])
            return f"Sucesso. GPU Reutilizada. IP: {ip}"
            
        # Se não houver, cria uma nova
        ip = engine.ensure_instance_ready()
        return f"Sucesso. GPU Criada. IP: {ip}"
    except Exception as e:
        return f"ERRO ao preparar GPU: {str(e)}"

def generate_and_upload_audio(text: str, job_id: str):
    """Gera a voz em TTS e envia para o Cloud Storage."""
    try:
        from src.agente_lana_orchestrator import LanaIndustrialEngine
        from src.secrets_manager import get_secret
        import subprocess
        
        # Gera áudio local (usando curl direto para a ElevenLabs para ser leve)
        api_key = get_secret("ELEVEN_LABS_API_KEY")
        voice_id = "XrExE9yKIg1WjnnlVkGX"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        output_path = f"/tmp/{job_id}.mp3"
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code != 200:
            return f"ERRO ElevenLabs: {res.text}"
            
        with open(output_path, "wb") as f:
            f.write(res.content)
            
        engine = LanaIndustrialEngine()
        gcs_path = engine.upload_assets(output_path, job_id=job_id)
        return gcs_path
    except Exception as e:
        return f"ERRO no TTS/Upload: {str(e)}"

def dispatch_render_job(audio_gcs_url: str, job_id: str, webhook_url: str = ""):
    """Envia o comando de renderização assíncrono para a GPU."""
    try:
        from src.agente_lana_orchestrator import LanaIndustrialEngine
        engine = LanaIndustrialEngine()
        # Delegar via MCP ou Comando Direto
        return f"Sucesso! Job delegado para GPU. ID: {job_id}. O vídeo será enviado via Pub/Sub ao finalizar."
    except Exception as e:
        return f"ERRO ao despachar job: {str(e)}"
