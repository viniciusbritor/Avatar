import sqlite3
import os

DB_PATH = "brasil_ai.db"

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de regionalismos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regionalismos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        termo_original TEXT NOT NULL UNIQUE,
        termo_corrigido TEXT NOT NULL,
        contexto TEXT,
        data_aprendizado DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Inserir exemplo solicitado pelo usuário
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO regionalismos (termo_original, termo_corrigido, contexto)
        VALUES ('escala 6 hora 1', 'escala 6 por 1', 'Terminologia de jornada de trabalho brasileira')
        """)
        cursor.execute("""
        INSERT OR IGNORE INTO regionalismos (termo_original, termo_corrigido, contexto)
        VALUES ('Brasil Ai', 'Brasil EiAi', 'Pronúncia fonética da marca')
        """)
        conn.commit()
    except Exception as e:
        print(f"Erro ao inserir dados iniciais: {e}")
        
    conn.close()
    print("Tabela 'regionalismos' configurada com sucesso em brasil_ai.db")

if __name__ == "__main__":
    setup_db()
