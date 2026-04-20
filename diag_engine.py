import torch
import os
import sys

def check():
    print("--- INICIANDO DIAGNÓSTICO LABORATORIAL (v12.5) ---")
    
    # 1. Hardware Check
    print(f"Python Version: {sys.version}")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    if cuda_available:
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # 2. Filesystem Check
    paths = {
        "UNet Checkpoint": "checkpoints/latentsync_unet.pt",
        "Config YAML": "configs/unet/second_stage.yaml",
        "Base Video": "lana_base_25fps.mp4",
        "Audio Source": "lana_audio_v7.mp3"
    }
    
    for name, path in paths.items():
        exists = os.path.exists(path)
        print(f"{name} ({path}): {'OK' if exists else 'MISSING'}")
        if exists:
            print(f"  Size: {os.path.getsize(path) / 1e6:.2f} MB")

    # 3. Import Check
    libs = ['omegaconf', 'matplotlib', 'diffusers', 'transformers', 'kornia', 'lpips', 'imageio', 'librosa']
    for lib in libs:
        try:
            __import__(lib)
            print(f"Library {lib}: OK")
        except ImportError as e:
            print(f"Library {lib}: FAILED - {str(e)}")

    print("--- FIM DO DIAGNÓSTICO ---")

if __name__ == "__main__":
    check()
