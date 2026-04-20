import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "registry.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de sessoes de producao
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS production_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        region TEXT,
        gpu_type TEXT,
        uptime_minutes REAL,
        estimated_cost_usd REAL,
        status TEXT,
        audio_ref TEXT
    )
    ''')
    
    # Tabela de configuracoes globais (metas de custo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Banco de dados inicializado em {DB_PATH}")

if __name__ == "__main__":
    init_db()
