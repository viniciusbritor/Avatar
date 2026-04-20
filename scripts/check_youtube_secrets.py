import sqlite3
import os

DB_PATH = "brasil_ai.db"

def check_youtube_secrets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM secrets WHERE key LIKE '%YOUTUBE%'")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print(row[0])

if __name__ == "__main__":
    check_youtube_secrets()
