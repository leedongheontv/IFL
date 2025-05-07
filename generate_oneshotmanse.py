import sqlite3
from db.mdbconn import SqliteDB
from datetime import datetime, timedelta

# 새 DB 생성
def create_new_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS oneshotmanse (
            solar_date TEXT PRIMARY KEY,
            year_ganji TEXT,
            month_ganji TEXT,
            day_ganji TEXT,
            hour_ganji TEXT,
            lunar_date TEXT,
            weekday TEXT,
            terms TEXT
        )
    ''')
    conn.commit()
    return conn, c

def main():
    start_date = datetime(1900, 1, 1)
    end_date = datetime(2050, 12, 31)
    db = SqliteDB('manseryuk.db')
    conn, c = create_new_db('oneshotmanse.db')
    total = (end_date - start_date).days + 1
    count = 0
    for i in range(total):
        date = start_date + timedelta(days=i)
        year, month, day = date.year, date.month, date.day
        birth_data = db.GetBirth(year, month, day)
        if birth_data:
            data = birth_data[0]
            # 시간은 0시 기준(자시)
            hour_data = db.GetTime(0)
            c.execute('''
                INSERT OR REPLACE INTO oneshotmanse (solar_date, year_ganji, month_ganji, day_ganji, hour_ganji, lunar_date, weekday, terms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date.strftime('%Y-%m-%d'),
                data[9],   # year_ganji
                data[11],  # month_ganji
                data[13],  # day_ganji
                hour_data[0] if hour_data else '',
                f"{data[5]}년 {data[6]}월 {data[7]}일",
                data[15],
                data[23] if data[23] else ''
            ))
            count += 1
        if i % 1000 == 0:
            print(f"{i}/{total} 처리 중...")
    conn.commit()
    conn.close()
    db.Close()
    print(f"완료! 총 {count}건 저장됨.")

if __name__ == '__main__':
    main() 