import sqlite3
conn = sqlite3.connect('C:/Users/vinic/brasil_ai.db')
row = conn.execute("SELECT value FROM secrets WHERE key = 'GITHUB_TOKEN'").fetchone()
if row:
    print(row[0])
conn.close()
