import sqlite3
import os

DB_PATH = "brasil_ai.db"

def list_tables_and_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table_name in tables:
        name = table_name[0]
        print(f"\nTable: {name}")
        cursor.execute(f"PRAGMA table_info({name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    conn.close()

if __name__ == "__main__":
    list_tables_and_columns()
