import whisper
import os

target_dir = "/workspace/latentsync/checkpoints/whisper"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

print(f"Downloading whisper tiny to {target_dir}...")
whisper.load_model("tiny", download_root=target_dir)
print("Success!")
