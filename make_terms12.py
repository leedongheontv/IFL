import sqlite3

terms_list = ('立春','驚蟄','淸明','立夏','芒種','小暑','立秋','白露','寒露','立冬','大雪','小寒')

conn = sqlite3.connect('db/manseryuk.db')
c = conn.cursor()

# 1. 새 테이블 생성
c.execute('''
CREATE TABLE IF NOT EXISTS terms12 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hterm TEXT,
    terms_time TEXT
)
''')

# 2. 기존 데이터에서 12절기만 추출하여 삽입
c.execute('DELETE FROM terms12')  # 기존 데이터 삭제(중복 방지)
placeholders = ','.join(['?'] * len(terms_list))
c.execute(f'''
    INSERT INTO terms12 (year, month, day, hterm, terms_time)
    SELECT cd_sy, cd_sm, cd_sd, cd_hterms, cd_terms_time
    FROM calenda_data
    WHERE cd_terms_time IS NOT NULL AND cd_terms_time != 'NULL'
      AND cd_hterms IN ({placeholders})
''', terms_list)

conn.commit()

# 3. 결과 확인
c.execute('SELECT * FROM terms12 ORDER BY year, month, day')
for row in c.fetchall():
    print(row)

conn.close() 