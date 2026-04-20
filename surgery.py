import os

files_to_patch = [
    "/workspace/latentsync/latentsync/utils/util.py",
    "/workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py"
]

for file_path in files_to_patch:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Remoções
        new_content = content.replace("-crf 18", "")
        new_content = new_content.replace('"-crf", "13"', "")
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Patched: {file_path}")
    else:
        print(f"File not found: {file_path}")
