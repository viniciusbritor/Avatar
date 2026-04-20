import sqlite3
conn = sqlite3.connect('brasil_ai.db')
c = conn.cursor()
c.execute("UPDATE pautas SET status = 'PENDENTE' WHERE status = 'SELECIONADA'")
conn.commit()
print(f'Pautas resetadas: {c.rowcount}')
conn.close()
