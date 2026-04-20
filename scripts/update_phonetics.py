import sqlite3
import os

DB_PATH = "brasil_ai.db"

def update_phonetics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Atualizar a pronúncia para Brasil Êi-Ai
    cursor.execute("""
    UPDATE regionalismos 
    SET termo_corrigido = 'Brasil Êi-Ai' 
    WHERE termo_original = 'Brasil Ai'
    """)
    
    # Inserir se não existir
    cursor.execute("""
    INSERT OR IGNORE INTO regionalismos (termo_original, termo_corrigido, contexto)
    VALUES ('Brasil Ai', 'Brasil Êi-Ai', 'Ajuste fino de pronúncia')
    """)
    
    conn.commit()
    conn.close()
    print("Pronuncia de marca atualizada para: Brasil Ei-Ai")

if __name__ == "__main__":
    update_phonetics()
