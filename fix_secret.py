import sqlite3
import subprocess
import os

try:
    conn = sqlite3.connect(r'C:\Users\vinic\brasil_ai.db')
    key = conn.execute("SELECT value FROM secrets WHERE key='GEMINI_API_KEY'").fetchone()[0]
    
    with open("gemini_tmp.txt", "w") as f:
        f.write(key)
        
    print("Enviando chave ao GCS Secrets...")
    subprocess.run("gcloud secrets create GEMINI_API_KEY --data-file=gemini_tmp.txt --project=brasili-ia-news", shell=True)
    subprocess.run("gcloud secrets versions add GEMINI_API_KEY --data-file=gemini_tmp.txt --project=brasili-ia-news", shell=True)
    
    os.remove("gemini_tmp.txt")
    print("Sucesso!")
except Exception as e:
    print(f"Erro: {e}")
