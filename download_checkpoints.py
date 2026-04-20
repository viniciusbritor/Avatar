from huggingface_hub import snapshot_download
import os

print("--- Iniciando Download Soberano de Checkpoints (V13.3) ---")
repo_id = 'ByteDance/LatentSync'
local_dir = os.path.expanduser('~/latentsync/checkpoints')

os.makedirs(local_dir, exist_ok=True)

snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)
print(f"--- Download Completo em {local_dir} ---")
