import sqlite3

conn = sqlite3.connect('db/manseryuk.db')
c = conn.cursor()
c.execute("SELECT DISTINCT cd_hterms FROM calenda_data WHERE cd_hterms IS NOT NULL AND cd_hterms != 'NULL'")
results = c.fetchall()
for row in results:
    print(row[0])
conn.close()