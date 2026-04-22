"""
secrets_manager.py — Brasil-AI
------------------------------
Gerencia credenciais e o banco SQLite com suporte dual:

  LOCAL  → SQLite puro  (sem dependências externas)
  CLOUD  → SQLite + GCS (sincroniza o .db com um bucket ao iniciar/finalizar)

Detecção automática de ambiente:
  - Se K_SERVICE estiver definida  → Cloud Run (modo CLOUD)
  - Se ENVIRONMENT=cloud           → forçar modo CLOUD
  - Caso contrário                 → modo LOCAL

Uso no código:
    from secrets_manager import get_secret
    api_key = get_secret("MINHA_API_KEY")
"""

import sqlite3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIGURAÇÃO DE AMBIENTE ────────────────────────────────────────────────

# Detecta automaticamente se está no Cloud Run (K_SERVICE é injetado pelo GCR)
IS_CLOUD = bool(os.getenv("K_SERVICE") or os.getenv("ENVIRONMENT") == "cloud")

# Caminho local do banco
DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "brasil_ai.db")))

# Configuração GCS (necessário apenas no modo cloud)
GCS_BUCKET  = os.getenv("GCS_BUCKET", "brasil-ia-lana-assets")
GCS_DB_BLOB = os.getenv("GCS_DB_BLOB", "brasil_ai.db")

_db_synced = False  # evita re-download na mesma sessão


# ─── SYNC GCS ────────────────────────────────────────────────────────────────

def _gcs_download():
    """Baixa o banco do GCS para o container (modo cloud)."""
    global _db_synced
    if _db_synced:
        return
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob   = bucket.blob(GCS_DB_BLOB)
        blob.download_to_filename(str(DB_PATH))
        print(f"   ☁️  [GCS] banco baixado: gs://{GCS_BUCKET}/{GCS_DB_BLOB}")
        _db_synced = True
    except Exception as e:
        print(f"   ⚠️  [GCS] Falha no download (novo banco será criado): {e}")
        _db_synced = True  # não tenta de novo


def gcs_upload():
    """
    Sobe o banco para o GCS após operações de escrita (modo cloud).
    Chamar explicitamente ao final do pipeline ou usar o decorator @with_gcs_sync.
    """
    if not IS_CLOUD:
        return
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob   = bucket.blob(GCS_DB_BLOB)
        blob.upload_from_filename(str(DB_PATH))
        print(f"   ☁️  [GCS] banco salvo: gs://{GCS_BUCKET}/{GCS_DB_BLOB}")
    except Exception as e:
        print(f"   ❌  [GCS] Falha no upload: {e}")


def _ensure_db():
    """Garante que o banco está disponível localmente."""
    if IS_CLOUD:
        _gcs_download()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ─── CONEXÃO ─────────────────────────────────────────────────────────────────

def _get_conn():
    _ensure_db()
    return sqlite3.connect(str(DB_PATH))


def _ensure_table():
    """Cria a tabela secrets se não existir."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                descricao  TEXT,
                updated_at DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()


# ─── API PÚBLICA ──────────────────────────────────────────────────────────────

def get_secret(key: str, fallback: str = "") -> str:
    """
    Retorna o valor de uma secret.
    Prioridade: SQLite (local ou GCS) → variável de ambiente → fallback.
    """
    _ensure_table()
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT value FROM secrets WHERE key = ?", (key,)
            ).fetchone()
            if row and row[0]:
                return row[0]
    except Exception as e:
        print(f"   ⚠️  [SECRETS] Erro ao ler '{key}': {e}")

    # Fallback: variável de ambiente
    env_val = os.getenv(key, fallback)
    return env_val


def set_secret(key: str, value: str, descricao: str = "", sync: bool = True):
    """
    Insere ou atualiza uma secret no banco.
    No modo cloud, faz upload automático após a escrita.
    """
    _ensure_table()
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO secrets (key, value, descricao, updated_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                descricao  = excluded.descricao,
                updated_at = excluded.updated_at
        """, (key, value, descricao))
        conn.commit()
    print(f"   ✅ Secret '{key}' salva.")
    if IS_CLOUD and sync:
        gcs_upload()


def list_secrets():
    """Lista todas as secrets cadastradas (sem mostrar os valores)."""
    _ensure_table()
    with _get_conn() as conn:
        return conn.execute(
            "SELECT key, descricao, updated_at FROM secrets ORDER BY key"
        ).fetchall()


def migrate_from_env():
    """Migra chaves do .env para o banco. Executar uma vez ao configurar o projeto."""
    _ensure_table()
    secrets_map = {
        "DID_BASIC_AUTH":           "D-ID — Basic Auth (Base64)",
        "DID_PRESENTER_ID":         "D-ID — Presenter ID da Lana",
        "YOUTUBE_CLIENT_ID":        "YouTube BrasilAI Full - Client ID",
        "YOUTUBE_CLIENT_SECRET":    "YouTube BrasilAI Full - Client Secret",
        "GEMINI_API_KEY":           "Google Gemini API Key",
        "GOOGLE_CLOUD_PROJECT":     "Google Cloud — Project ID",
        "GOOGLE_CLOUD_LOCATION":    "Google Cloud — Region",
        "KLING_ACCESS_KEY":         "Kling AI — Access Key",
        "KLING_SECRET_KEY":         "Kling AI — Secret Key",
    }

    env_label = "☁️  CLOUD (SQLite + GCS)" if IS_CLOUD else "💻 LOCAL (SQLite)"
    print(f"\n🔐 Modo: {env_label}")
    print(f"📍 Banco: {DB_PATH.resolve()}")
    print("─" * 50)

    ok = 0
    for key, desc in secrets_map.items():
        val = os.getenv(key, "")
        if val:
            set_secret(key, val, desc, sync=False)
            ok += 1
        else:
            print(f"   '{key}' não encontrada no .env — pulada.")

    print(f"\n{ok}/{len(secrets_map)} secrets migradas.")

    # Um único upload ao final (evita N chamadas à GCS)
    if IS_CLOUD:
        gcs_upload()


# ─── CLI ─────────────────────────────────────────────────────────────────────

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# CLI para gerenciamento rápido via terminal
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerenciador de Segredos Brasil-AI")
    parser.add_argument("--list", action="store_true", help="Listar chaves cadastradas")
    parser.add_argument("--set", nargs=3, metavar=("KEY", "VALUE", "DESC"), help="Definir uma nova chave")
    parser.add_argument("--get", metavar="KEY", help="Consultar valor de uma chave (mascarado)")
    parser.add_argument("--migrate", action="store_true", help="Migrar chaves do .env para o banco")

    args = parser.parse_args()

    env_label = "MODO ENV (.env)" if not os.path.exists(DB_PATH) else "MODO BANCO (SQLite)"
    # v21.1.0: Sem emojis que quebram no Windows CMD
    print(f"Modo: {env_label}  |  Banco: {DB_PATH.resolve()}")

    if "--migrate" in sys.argv:
        migrate_from_env()

    elif "--list" in sys.argv:
        rows = list_secrets()
        if not rows:
            print("Nenhuma secret cadastrada.")
        else:
            print(f"\n{'CHAVE':<35} {'DESCRIÇÃO':<45} ATUALIZADO")
            print("─" * 100)
            for key, desc, upd in rows:
                print(f"{key:<35} {(desc or ''):<45} {upd}")

    elif "--set" in sys.argv:
        args = sys.argv[sys.argv.index("--set") + 1:]
        if len(args) >= 2:
            set_secret(args[0], args[1], args[2] if len(args) > 2 else "")
        else:
            print("Uso: python secrets_manager.py --set CHAVE VALOR [descricao]")

    elif "--get" in sys.argv:
        args = sys.argv[sys.argv.index("--get") + 1:]
        if args:
            val = get_secret(args[0])
            masked = ("*" * (len(val) - 4) + val[-4:]) if len(val) > 4 else "(vazia)"
            print(f"{args[0]} = {masked}")
        else:
            print("Uso: python secrets_manager.py --get CHAVE")

    elif "--sync-up" in sys.argv:
        gcs_upload()

    else:
        print("\nUso:")
        print("  --migrate          migra .env → banco")
        print("  --list             lista chaves cadastradas")
        print("  --get  CHAVE       consulta valor (mascarado)")
        print("  --set  K V [D]     define/atualiza chave")
        print("  --sync-up          força upload do banco para GCS (cloud)")
        print("\nVariáveis de ambiente:")
        print("  K_SERVICE          detectado automaticamente pelo Cloud Run")
        print("  ENVIRONMENT=cloud  força modo cloud manualmente")
        print("  GCS_BUCKET         nome do bucket (padrão: brasil-ai-db)")
        print("  DB_PATH            caminho local do banco")
