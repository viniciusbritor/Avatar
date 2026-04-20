import sqlite3
import os

DB_PATH = "brasil_ai.db"

def find_master_keys():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Search for anything that might be a master key in key or value
    cursor.execute("SELECT key, value FROM secrets")
    rows = cursor.fetchall()
    conn.close()
    
    found = False
    for key, val in rows:
        if "master" in key.lower() or "master" in val.lower():
            print(f"FOUND KEY: {key}")
            print(f"  Preview: {val[:100]}...")
            found = True
            
    if not found:
        print("Nenhuma chave com o termo 'master' encontrada nas tabelas de segredos ou config.")

if __name__ == "__main__":
    find_master_keys()
