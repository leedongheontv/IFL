from flask import Flask, render_template, request, jsonify
from db.mdbconn import SqliteDB
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

def get_saju_data(year, month, day, hour):
    try:
        # 현재 파일의 절대 경로를 기준으로 데이터베이스 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, 'db', 'manseryuk.db')
        
        # 데이터베이스 파일 존재 여부 확인
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return None
            
        db = SqliteDB('manseryuk.db')
        birth_data = db.GetBirth(year, month, day)
        
        if not birth_data:
            print(f"No data found for date: {year}-{month}-{day}")
            return None
        
        # 시간 정보 가져오기
        time_data = db.GetTime(hour)
        
        if birth_data:
            data = birth_data[0]  # 첫 번째 결과 사용
            print("[DEBUG] data 전체:", data)  # 이 줄 추가

            # 절기 카운팅 값 계산 (terms12 테이블 활용)
            terms_count = {'prev': 0, 'next': 0}
            current_date = datetime(year, month, day)
            # 이전 12절기
            prev_terms = db.GetPrevTerms12(year, month, day)
            if prev_terms and prev_terms[4]:
                prev_terms_time = prev_terms[4]
                prev_terms_year = int(prev_terms_time[:4])
                prev_terms_month = int(prev_terms_time[4:6])
                prev_terms_day = int(prev_terms_time[6:8])
                prev_terms_hour = int(prev_terms_time[8:10])
                prev_terms_minute = int(prev_terms_time[10:12])
                prev_terms_date = datetime(prev_terms_year, prev_terms_month, prev_terms_day, prev_terms_hour, prev_terms_minute)
                terms_count['prev'] = (current_date - prev_terms_date).days
                print(f"[DEBUG] prev_terms: {prev_terms_year}-{prev_terms_month:02d}-{prev_terms_day:02d} {prev_terms[3]}")
            else:
                print("[DEBUG] prev_terms: None")
            # 다음 12절기
            next_terms = db.GetNextTerms12(year, month, day)
            if next_terms and next_terms[4]:
                next_terms_time = next_terms[4]
                next_terms_year = int(next_terms_time[:4])
                next_terms_month = int(next_terms_time[4:6])
                next_terms_day = int(next_terms_time[6:8])
                next_terms_hour = int(next_terms_time[8:10])
                next_terms_minute = int(next_terms_time[10:12])
                next_terms_date = datetime(next_terms_year, next_terms_month, next_terms_day, next_terms_hour, next_terms_minute)
                terms_count['next'] = (next_terms_date - current_date).days
                print(f"[DEBUG] next_terms: {next_terms_year}-{next_terms_month:02d}-{next_terms_day:02d} {next_terms[3]}")
            else:
                print("[DEBUG] next_terms: None")
            
            # 데이터베이스 연결 종료
            db.Close()
            
            return {
                'year_ganji': data[8],   # 년간지(한자)
                'month_ganji': data[10], # 월간지(한자)
                'day_ganji': data[12],   # 일간지(한자)
                'hour_ganji': time_data[0] if time_data else '',  # 시간간지
                'lunar_date': f"{data[5]}년 {data[6]}월 {data[7]}일",  # 음력 날짜
                'solar_date': f"{data[2]}년 {data[3]}월 {data[4]}일",  # 양력 날짜
                'weekday': data[15],  # 요일
                'terms': data[21] if data[21] and data[21] != 'NULL' else '',  # cd_hterms (한문 24절기)
                'terms_count': terms_count  # 절기 카운팅 값 추가
            }
    except Exception as e:
        print(f"Error in get_saju_data: {str(e)}")
        return None
    return None

def get_hour_pillar(day_ganji, hour, minute):
    # 한자만 추출 (예: '壬子' -> '壬')
    hanja_gan = day_ganji[0]
    # 시주 규칙 정의
    rules = [
        ((23,30,1,29),  ["甲子", "丙子", "戊子", "庚子", "壬子"]),
        ((1,30,3,29),   ["乙丑", "丁丑", "己丑", "辛丑", "癸丑"]),
        ((3,30,5,29),   ["丙寅", "戊寅", "庚寅", "壬寅", "甲寅"]),
        ((5,30,7,29),   ["丁卯", "己卯", "辛卯", "癸卯", "乙卯"]),
        ((7,30,9,29),   ["戊辰", "庚辰", "壬辰", "甲辰", "丙辰"]),
        ((9,30,11,29),  ["己巳", "辛巳", "癸巳", "乙巳", "丁巳"]),
        ((11,30,13,29), ["庚午", "壬午", "甲午", "丙午", "戊午"]),
        ((13,30,15,29), ["辛未", "癸未", "乙未", "丁未", "己未"]),
        ((15,30,17,29), ["壬申", "甲申", "丙申", "戊申", "庚申"]),
        ((17,30,19,29), ["癸酉", "乙酉", "丁酉", "己酉", "辛酉"]),
        ((19,30,21,29), ["甲戌", "丙戌", "戊戌", "庚戌", "壬戌"]),
        ((21,30,23,29), ["乙亥", "丁亥", "己亥", "辛亥", "癸亥"]),
    ]
    # 일간지별 인덱스
    day_ganji_map = {
        "甲":0, "己":0,
        "乙":1, "庚":1,
        "丙":2, "辛":2,
        "丁":3, "壬":3,
        "戊":4, "癸":4
    }
    # 23:30~23:59는 다음날로 넘김
    if (hour == 23 and minute >= 30):
        return 'NEXT_DAY'
    # 규칙 적용
    for (h1, m1, h2, m2), ganji_list in rules:
        # 시간 범위 체크
        after_start = (hour > h1) or (hour == h1 and minute >= m1)
        before_end = (hour < h2) or (hour == h2 and minute <= m2)
        if after_start and before_end:
            idx = day_ganji_map.get(hanja_gan, None)
            if idx is not None:
                return ganji_list[idx]
            else:
                print(f"[DEBUG] 일간지({hanja_gan})가 규칙에 없습니다.")
                return ''
    print(f"[DEBUG] 시간({hour}:{minute})이 어떤 시주 구간에도 해당하지 않습니다.")
    return ''

def calculate_daewoon(gender, year_ganji, month_ganji, terms_count):
    """
    대운수 계산 함수
    gender: 'M' (남자) 또는 'F' (여자)
    year_ganji: 년간지 (예: '甲寅')
    month_ganji: 월간지 (예: '甲寅')
    terms_count: 절기 카운팅 값 (이전 절기 또는 다음 절기까지의 카운트)
    """
    # 천간 순서
    gan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    # 지지 순서
    ji = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 년간과 월간지에서 천간 분리
    year_gan = year_ganji[0]
    month_gan = month_ganji[0]
    month_ji = month_ganji[1]
    
    # 대운 시작 나이 계산 (남자는 1, 여자는 11)
    start_age = 1 if gender == 'M' else 11
    
    # 년간에 따른 대운 방향 결정
    yang_gan = ['甲', '丙', '戊', '庚', '壬']  # 양간
    yin_gan = ['乙', '丁', '己', '辛', '癸']   # 음간
    
    # 년간과 성별에 따른 대운수 계산
    if (gender == 'M' and year_gan in yang_gan) or (gender == 'F' and year_gan in yin_gan):
        # 다음 절기까지의 카운팅 값을 3으로 나눈 몫
        daewoon_count = terms_count['next'] // 3
    else:
        # 이전 절기까지의 카운팅 값을 3으로 나눈 몫
        daewoon_count = terms_count['prev'] // 3
    # 규칙 추가: 3으로 나눈 값이 10을 넘으면 그대로, 3 이하이면 1로 한다.
    if daewoon_count <= 3:
        daewoon_count = 1
    # (10이 넘을 경우는 그대로)
    
    # 기본 방향 설정 (남자는 순행, 여자는 역행)
    base_direction = 1 if gender == 'M' else -1
    
    # 년간에 따른 방향 조정
    if year_gan in yang_gan:
        # 양간: 남자는 순행, 여자는 역행
        direction = base_direction
    else:  # 음간
        # 음간: 남자는 역행, 여자는 순행
        direction = -base_direction
    
    # 월간지의 천간과 지지 인덱스 찾기
    gan_idx = gan.index(month_gan)
    ji_idx = ji.index(month_ji)
    
    # 대운 계산 (10개)
    daewoon_list = []
    for i in range(10):
        # 새로운 천간과 지지 인덱스 계산
        new_gan_idx = (gan_idx + (i * direction)) % 10
        new_ji_idx = (ji_idx + (i * direction)) % 12
        
        # 대운 간지 생성
        daewoon = gan[new_gan_idx] + ji[new_ji_idx]
        
        # 시작 나이와 종료 나이 계산
        start = start_age + (i * 10)
        end = start + 9
        
        daewoon_list.append({
            'ganji': daewoon,
            'age_range': f"{start}~{end}세",
            'daewoon_count': daewoon_count
        })
    
    return daewoon_list

def convert_lunar_to_solar(year, month, day):
    """
    음력 날짜를 양력 날짜로 변환하는 함수
    """
    try:
        db = SqliteDB('manseryuk.db')
        # 음력 날짜로 데이터 조회
        query = "SELECT cd_sy, cd_sm, cd_sd FROM calenda_data WHERE cd_ly=? AND cd_lm=? AND cd_ld=?"
        db.c.execute(query, (year, month, day))
        result = db.c.fetchone()
        db.Close()
        
        if result:
            # int로 변환해서 반환
            return {
                'year': int(result[0]),
                'month': int(result[1]),
                'day': int(result[2])
            }
        return None
    except Exception as e:
        print(f"Error in convert_lunar_to_solar: {str(e)}")
        return None

def get_sibsin(day_gan, target, is_gan=True):
    """
    day_gan: 일간(한자, 예: '甲')
    target: 대상 천간 또는 지지(한자)
    is_gan: True면 천간(윗줄), False면 지지(아랫줄)
    """
    sibsin_gan = {
        '甲': ['비견','겁재','식신','상관','편재','정재','편관','정관','편인','정인'],
        '乙': ['겁재','비견','상관','식신','정재','편재','정관','편관','정인','편인'],
        '丙': ['편인','정인','비견','겁재','식신','상관','편재','정재','편관','정관'],
        '丁': ['정인','편인','겁재','비견','상관','식신','정재','편재','정관','편관'],
        '戊': ['편관','정관','편인','정인','비견','겁재','식신','상관','편재','정재'],
        '己': ['정관','편관','정인','편인','겁재','비견','상관','식신','정재','편재'],
        '庚': ['편재','정재','편관','정관','편인','정인','비견','겁재','식신','상관'],
        '辛': ['정재','편재','정관','편관','정인','편인','겁재','비견','상관','식신'],
        '壬': ['식신','상관','편재','정재','편관','정관','편인','정인','비견','겁재'],
        '癸': ['상관','식신','정재','편재','정관','편관','정인','편인','겁재','비견'],
    }
    sibsin_ji = {
        '甲': ['정인','정재','비견','겁재','편재','식신','상관','정재','편관','정관','편재','편인'],
        '乙': ['편인','편재','겁재','비견','정재','상관','식신','편재','정관','편관','정재','정인'],
        '丙': ['정관','상관','편인','정인','식신','비견','겁재','상관','편재','정재','식신','편관'],
        '丁': ['편관','식신','정인','편인','상관','겁재','비견','식신','정재','편재','상관','정관'],
        '戊': ['정재','겁재','편관','정관','비견','편인','정인','겁재','식신','상관','비견','편재'],
        '己': ['편재','비견','편관','정관','겁재','정인','편인','비견','상관','식신','겁재','정재'],
        '庚': ['상관','정인','편재','정재','편인','편관','정관','정인','비견','겁재','편인','식신'],
        '辛': ['식신','편인','정재','편재','정인','정관','편관','편인','겁재','비견','정인','상관'],
        '壬': ['겁재','정관','식신','상관','편관','편재','정재','정관','편인','정인','편관','비견'],
        '癸': ['비견','편관','상관','식신','정관','정재','편재','편관','정인','편인','정관','겁재'],
    }
    gan_list = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    ji_list = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    if not target or len(target) != 1:
        return ''
    if is_gan:
        if target not in gan_list:
            return ''
        idx = gan_list.index(target)
        return sibsin_gan[day_gan][idx]
    else:
        if target not in ji_list:
            return ''
        idx = ji_list.index(target)
        return sibsin_ji[day_gan][idx]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_saju', methods=['POST'])
def get_saju():
    try:
        data = request.get_json()
        is_lunar = data.get('is_lunar', False)  # 음력 여부
        unknown_hour = data.get('unknown_hour', False)  # 시 모름 여부
        year = int(data.get('year'))
        month = int(data.get('month'))
        day = int(data.get('day'))
        hour = int(data.get('hour', 0))
        minute = int(data.get('minute', 0))
        gender = data.get('gender', 'M')  # 기본값은 남자

        # 음력 입력인 경우 양력으로 변환
        if is_lunar:
            solar_date = convert_lunar_to_solar(year, month, day)
            if not solar_date:
                return jsonify({'error': '음력 날짜를 찾을 수 없습니다.'}), 404
            year, month, day = solar_date['year'], solar_date['month'], solar_date['day']

        # 23:30~23:59는 다음날로 넘김
        next_day = False
        if hour == 23 and minute >= 30:
            dt = datetime(year, month, day) + timedelta(days=1)
            year, month, day = dt.year, dt.month, dt.day
            hour, minute = 0, 0
            next_day = True

        saju_data = get_saju_data(year, month, day, hour)
        if saju_data:
            # 시주 계산 (먼저!)
            if unknown_hour:
                saju_data['hour_ganji'] = ''
                saju_data['input_hour'] = '시 모름'
            else:
                day_ganji = saju_data['day_ganji']
                print(f"[DEBUG] day_ganji 값: {day_ganji}")
                hour_pillar = get_hour_pillar(day_ganji, hour, minute)
                if hour_pillar == 'NEXT_DAY':
                    day_ganji = saju_data['day_ganji']
                    hour_pillar = get_hour_pillar(day_ganji, hour, minute)
                saju_data['hour_ganji'] = hour_pillar
                saju_data['input_hour'] = f"{hour:02d}:{minute:02d}"

            # 십신 정보 추가 (시주가 결정된 후에!)
            sibsin = {}
            year_gan = saju_data['year_ganji'][0] if saju_data['year_ganji'] and len(saju_data['year_ganji']) > 0 else ''
            year_ji = saju_data['year_ganji'][1] if saju_data['year_ganji'] and len(saju_data['year_ganji']) > 1 else ''
            month_gan = saju_data['month_ganji'][0] if saju_data['month_ganji'] and len(saju_data['month_ganji']) > 0 else ''
            month_ji = saju_data['month_ganji'][1] if saju_data['month_ganji'] and len(saju_data['month_ganji']) > 1 else ''
            day_gan = saju_data['day_ganji'][0] if saju_data['day_ganji'] and len(saju_data['day_ganji']) > 0 else ''
            day_ji = saju_data['day_ganji'][1] if saju_data['day_ganji'] and len(saju_data['day_ganji']) > 1 else ''
            hour_gan = saju_data['hour_ganji'][0] if saju_data['hour_ganji'] and len(saju_data['hour_ganji']) > 0 else ''
            hour_ji = saju_data['hour_ganji'][1] if saju_data['hour_ganji'] and len(saju_data['hour_ganji']) > 1 else ''
            sibsin['year_gan'] = get_sibsin(day_gan, year_gan, True)
            sibsin['year_ji'] = get_sibsin(day_gan, year_ji, False)
            sibsin['month_gan'] = get_sibsin(day_gan, month_gan, True)
            sibsin['month_ji'] = get_sibsin(day_gan, month_ji, False)
            sibsin['day_gan'] = get_sibsin(day_gan, day_gan, True)
            sibsin['day_ji'] = get_sibsin(day_gan, day_ji, False)
            sibsin['hour_gan'] = get_sibsin(day_gan, hour_gan, True) if hour_gan else ''
            sibsin['hour_ji'] = get_sibsin(day_gan, hour_ji, False) if hour_ji else ''
            saju_data['sibsin'] = sibsin
            # 대운수 계산 추가 (년간지와 절기 카운팅 값도 전달)
            saju_data['daewoon'] = calculate_daewoon(
                gender, 
                saju_data['year_ganji'], 
                saju_data['month_ganji'],
                saju_data.get('terms_count', {'prev': 0, 'next': 0})
            )
            return jsonify(saju_data)
        return jsonify({'error': '데이터를 찾을 수 없습니다.'}), 404
    except Exception as e:
        print(f"Error in get_saju route: {str(e)}")
        return jsonify({'error': '서버 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    app.run(debug=True) 