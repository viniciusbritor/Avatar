import os
import subprocess
import sqlite3
import time
import sys

# Garante UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Configurações
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, "workspace_brasil_ia")
LANGGRAPH_SCRIPT = os.path.join(ROOT_DIR, "workflows", "brasil_ia_langgraph_pipeline.py")

def get_pending_folders():
    """Lista pastas de pautas que estao prontas."""
    pending = []
    # Pautas alvo. A ordem definirá quais tentaremos subir caso tenha limite.
    targets = ["p_6472", "p_6513", "p_6475", "p_6512"]
    
    for folder in targets:
        path = os.path.join(WORKSPACE_DIR, folder)
        if os.path.exists(path):
            pending.append(f"workspace_brasil_ia/{folder}")
    return pending

def run_batch():
    pending = get_pending_folders()
    if not pending:
        print("📭 Nenhuma pauta pendente encontrada.")
        return

    print(f"🚀 Iniciando verificação e upload de {len(pending)} pautas alvo...")
    
    for folder in pending:
        print(f"\n--- Avaliando: {folder} ---")
        
        manifest_path = os.path.join(ROOT_DIR, folder, "09_upload_manifest.json")
        
        
        # Extrair ID da pauta (ex: "p_6472" -> "6472")
        pauta_id = folder.split('_')[-1]

        # 1. Se manifest já existe, o video já foi postado! Vamos tentar repostar a thumbnail se falhou.
        if os.path.exists(manifest_path):
            print(f"📦 Vídeo {pauta_id} já postado. Executando RetryThumbnail via LangGraph...")
            cmd_thumb = ["python", LANGGRAPH_SCRIPT, pauta_id, "--stage", "11"]
            result_thumb = subprocess.run(cmd_thumb, capture_output=True, text=True, encoding='utf-8')
            print(result_thumb.stdout.strip())
            # Não aborta se a thumbal falhar, segue para a próxima notícia.
            if "forbidden" in result_thumb.stdout or "limite" in result_thumb.stdout.lower() or "insufficient" in result_thumb.stdout.lower():
                print("⚠️ A subida de thumbnails customizadas ainda está bloqueada/indisponível.")
            continue
            
        # 2. Se manifest NÃO existe, tentar upload da notícia
        print(f"▶️ Vídeo {pauta_id} novo. Disparando Upload Oficial via LangGraph...")
        cmd_upload = ["python", LANGGRAPH_SCRIPT, pauta_id, "--stage", "10"]
        result_up = subprocess.run(cmd_upload, capture_output=True, text=True, encoding='utf-8')
        
        if result_up.stdout:
            print(result_up.stdout.strip())
        if result_up.stderr:
            print(result_up.stderr.strip())
        
        # Monitora se esbarramos em quota / limit exceeded
        output_lower = (result_up.stdout + result_up.stderr).lower()
        if "uploadlimitexceeded" in output_lower or "quota" in output_lower:
            print("❌ Limite diário de upload do YouTube atingido. Abortando lote.")
            return False
            
        if "Video publicado" in result_up.stdout or "videoId" in result_up.stdout:
            print(f"✅ Sucesso no comando principal para {folder}!")
        else:
            print(f"⚠️ Aviso inesperado ao processar {folder}.")
            
    print("\n🏁 Processamento em lote finalizado.")
    return True

if __name__ == "__main__":
    run_batch()
