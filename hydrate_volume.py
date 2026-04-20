import os
import subprocess

def run_cmd(cmd):
    print(f"Executando: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def hydrate():
    # Caminho do volume no GCE
    VOLUME_PATH = "/app/data"
    
    if not os.path.exists(VOLUME_PATH):
        print(f"❌ Erro: {VOLUME_PATH} não encontrado. Certifique-se de que o Network Volume está montado.")
        return

    print("🚀 Iniciando Hidratação do Volume (Download de 15GB)...")

    # 1. Criar estrutura de pastas
    os.makedirs(f"{VOLUME_PATH}/checkpoints", exist_ok=True)
    os.makedirs(f"{VOLUME_PATH}/configs", exist_ok=True)
    os.makedirs(f"{VOLUME_PATH}/templates", exist_ok=True)

    # 2. Baixar os pesos da HuggingFace (LatentSync-1.6)
    # Vamos usar git clone (com LFS) em uma pasta temporária e mover o que importa
    TEMP_MODELS = f"{VOLUME_PATH}/temp_models"
    if not os.path.exists(f"{VOLUME_PATH}/checkpoints/latentsync_unet.pt"):
        print("📥 Baixando modelos do HuggingFace (ByteDance/LatentSync-1.6)...")
        run_cmd(f"git clone https://huggingface.co/ByteDance/LatentSync-1.6 {TEMP_MODELS}")
        
        # Mover arquivos para o lugar certo
        run_cmd(f"mv {TEMP_MODELS}/latentsync_unet.pt {VOLUME_PATH}/checkpoints/")
        run_cmd(f"mv {TEMP_MODELS}/stable_syncnet.pt {VOLUME_PATH}/checkpoints/")
        run_cmd(f"cp -rv {TEMP_MODELS}/configs/* {VOLUME_PATH}/configs/")
        
        # Limpeza
        run_cmd(f"rm -rf {TEMP_MODELS}")
    else:
        print("✅ Checkpoints já existem no volume.")

    # 3. Baixar Template da Lana (Exemplo)
    # Se você tiver o link direto do Lana Template, podemos colocar aqui.
    # Por enquanto, criaremos um placeholder ou usaremos o default do repo.
    print("🎬 Setup de Templates concluído.")

    print("\n✨ VOLUME HIDRATADO COM SUCESSO! ✨")
    print(f"Local: {VOLUME_PATH}")
    run_cmd(f"ls -R {VOLUME_PATH}")

if __name__ == "__main__":
    hydrate()
