import sqlite3
import os
from pathlib import Path
from typing import Optional

# [SINGLETON] Central Vault Location
CENTRAL_DB_PATH = Path(r"C:\Users\vinic\brasil_ai.db")

def get_secret(key: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Busca uma chave no Banco de Secrets Centralizado.
    Se não encontrar, tenta ler de variáveis de ambiente.
    """
    # 1. Tentar Banco Central
    if CENTRAL_DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(CENTRAL_DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM secrets WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception as e:
            print(f"[SecretsManager] Erro ao ler banco central: {e}")

    # 2. Tentar Variável de Ambiente
    env_val = os.getenv(key)
    if env_val:
        return env_val

    # 3. Fallback
    return fallback

def set_secret(key: str, value: str, description: str = ""):
    """Insere ou atualiza uma chave no Banco Central."""
    conn = sqlite3.connect(str(CENTRAL_DB_PATH))
    conn.execute("""
        INSERT INTO secrets (key, value, descricao, updated_at)
        VALUES (?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            descricao = excluded.descricao,
            updated_at = excluded.updated_at
    """, (key, value, description))
    conn.commit()
    conn.close()
    print(f"[SecretsManager] Chave '{key}' atualizada no banco central.")

if __name__ == "__main__":
    # Teste rápido
    test_key = "GEMINI_API_KEY"
    val = get_secret(test_key)
    print(f"Teste {test_key}: {'[FOUND]' if val else '[NOT FOUND]'}")
