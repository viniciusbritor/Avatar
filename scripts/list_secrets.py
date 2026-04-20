import sqlite3
import os

DB_PATH = "brasil_ai.db"

def list_all_secrets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM secrets")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        key = row[0]
        val = row[1]
        # Mask secrets
        masked_val = val[:5] + "..." + val[-5:] if len(val) > 10 else "***"
        print(f"{key}: {masked_val}")

if __name__ == "__main__":
    list_all_secrets()
