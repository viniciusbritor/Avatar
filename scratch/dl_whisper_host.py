import whisper
import os
import shutil

print("Installing model 'tiny'...")
model = whisper.load_model("tiny")
cache_path = os.path.expanduser("~/.cache/whisper/tiny.pt")
target_path = "/mnt/weights/whisper/tiny.pt"

os.makedirs("/mnt/weights/whisper", exist_ok=True)
if os.path.exists(cache_path):
    print(f"Moving {cache_path} to {target_path}...")
    shutil.copy(cache_path, target_path)
    print("Success!")
else:
    print("Error: tiny.pt not found in cache.")
