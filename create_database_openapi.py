
### 1.필요한 라이브러리 / 모듈 / 함수 임포트
import os, sqlite3, requests, time
from dotenv import load_dotenv


### 2. 환경 설정

# 실행 파일 폴더 경로 가져오기
folder_path = os.path.dirname(os.path.abspath(__file__))

# 서울 열린데이터광장 API Key 가져오기
env_file_path=os.path.join(folder_path, '.env')
load_dotenv(env_file_path)


### 3. API 데이터 수집 함수 정의
def fetch_sales_data(api_key, start_index, end_index, period):
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/VwsmTrdarSelngQq/{start_index}/{end_index}/{period}"
    try:
        response = requests.get(url, timeout=60)
        # 요청이 성공적으로 처리되었는지 확인
        # HTTP 상태 코드가 200번대가 아니면 (404 Not Found, 500 Server Error 등) HTTPError를 발생시킴        
        response.raise_for_status()
        # 서버로부터 받은 JSON 문자열을 파이썬 딕셔너리로 변환
        data = response.json()
        # 데이터 수집
        if 'VwsmTrdarSelngQq' in data and 'row' in data['VwsmTrdarSelngQq']:
            return data['VwsmTrdarSelngQq']['row']
        elif 'RESULT' in data and data['RESULT']['CODE'] == 'INFO-200': return []
        else:
            error_message = data.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류')
            print(f"API 에러: {error_message}")
            if '인증키' in error_message: return "AUTH_ERROR"
            return None
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None


### 4. sqlite3 DB 파일 및 테이블 생성 함수 정의
def initialize_database(db_path='sales.db'):
    print(f"데이터베이스 '{db_path}' 파일을 확인하고, 없으면 생성합니다...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quarterly_sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year_quarter TEXT NOT NULL,
        district_type TEXT, district_code TEXT NOT NULL, district_name TEXT,
        service_category_code TEXT, service_category_name TEXT,
        monthly_sales_amount INTEGER, monthly_sales_count INTEGER,
        weekday_sales_amount INTEGER, weekend_sales_amount INTEGER,
        sales_monday INTEGER, sales_tuesday INTEGER, sales_wednesday INTEGER,
        sales_thursday INTEGER, sales_friday INTEGER, sales_saturday INTEGER, sales_sunday INTEGER,
        sales_time_00_06 INTEGER, sales_time_06_11 INTEGER, sales_time_11_14 INTEGER,
        sales_time_14_17 INTEGER, sales_time_17_21 INTEGER, sales_time_21_24 INTEGER,
        male_sales_amount INTEGER, female_sales_amount INTEGER,
        sales_by_age_10s INTEGER, sales_by_age_20s INTEGER,
        sales_by_age_30s INTEGER, sales_by_age_40s INTEGER,
        sales_by_age_50s INTEGER, sales_by_age_60s_above INTEGER,
        UNIQUE(year_quarter, district_code, service_category_code)
    )
    ''')
    # 변경 사항 저장
    conn.commit()
    # DB 연결 종료
    conn.close()
    print("데이터베이스 테이블 준비가 완료되었습니다.")


### 5. 특정 기간 데이터 수집 및 DB 업데이트 함수 정의 
def update_database_for_period(db_path, api_key, year, quarter):
    period = f"{year}{quarter}"
    print(f"--- {year}년 {quarter}분기 (요청 코드: {period}) 데이터 수집 및 업데이트 시작 ---")
    start, end, total_inserted = 1, 1000, 0
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    while True:
        print(f"{start} ~ {end} 범위의 데이터를 요청합니다...")
        rows = fetch_sales_data(api_key, start, end, period)
        if rows == "AUTH_ERROR": 
            return False
        if not rows: 
            break
        
        # 실제 API 응답인 영문 필드명을 사용하여 데이터 추출
        data_to_insert = [(
            f"{year}{quarter}",
            r['TRDAR_SE_CD_NM'], r['TRDAR_CD'], r['TRDAR_CD_NM'],
            r['SVC_INDUTY_CD'], r['SVC_INDUTY_CD_NM'],
            r['THSMON_SELNG_AMT'], r['THSMON_SELNG_CO'],
            r['MDWK_SELNG_AMT'], r['WKEND_SELNG_AMT'],
            r['MON_SELNG_AMT'], r['TUES_SELNG_AMT'], r['WED_SELNG_AMT'],
            r['THUR_SELNG_AMT'], r['FRI_SELNG_AMT'], r['SAT_SELNG_AMT'], r['SUN_SELNG_AMT'],
            r['TMZON_00_06_SELNG_AMT'], r['TMZON_06_11_SELNG_AMT'], r['TMZON_11_14_SELNG_AMT'],
            r['TMZON_14_17_SELNG_AMT'], r['TMZON_17_21_SELNG_AMT'], r['TMZON_21_24_SELNG_AMT'],
            r['ML_SELNG_AMT'], r['FML_SELNG_AMT'],
            r['AGRDE_10_SELNG_AMT'], r['AGRDE_20_SELNG_AMT'],
            r['AGRDE_30_SELNG_AMT'], r['AGRDE_40_SELNG_AMT'],
            r['AGRDE_50_SELNG_AMT'], r['AGRDE_60_ABOVE_SELNG_AMT']
        ) for r in rows]
        
        # 추출된 데이터 -> DB 테이블에 저장
        cursor.executemany("""INSERT OR IGNORE INTO quarterly_sales (
               year_quarter, district_type, district_code, district_name,
               service_category_code, service_category_name,
               monthly_sales_amount, monthly_sales_count,
               weekday_sales_amount, weekend_sales_amount,
               sales_monday, sales_tuesday, sales_wednesday, sales_thursday,
               sales_friday, sales_saturday, sales_sunday,
               sales_time_00_06, sales_time_06_11, sales_time_11_14,
               sales_time_14_17, sales_time_17_21, sales_time_21_24,
               male_sales_amount, female_sales_amount,
               sales_by_age_10s, sales_by_age_20s, sales_by_age_30s,
               sales_by_age_40s, sales_by_age_50s, sales_by_age_60s_above
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data_to_insert)
        
        # 변경 사항 저장
        conn.commit()

        inserted_count = cursor.rowcount or 0
        total_inserted += inserted_count
        print(f"-> {len(rows)}건 확인, {inserted_count}건 신규 삽입.")

        # 종료 조건
        if len(rows) < 1000: 
            break

        # 다음 시작 / 끝 인덱스 설정
        start += 1000
        end += 1000
        time.sleep(0.1)
    print(f"--- {year}년 {quarter}분기 업데이트 완료. 총 {total_inserted}건 신규 데이터 추가 ---")

    # DB 연결 종료
    conn.close()
    return True


### 6. 애플리케이션 실행
if __name__ == '__main__':
    api_key = os.getenv("SEOUL_DATA_API_KEY")
    db_path = 'sales.db'
    if not api_key: 
        print("환경변수에서 SEOUL_DATA_API_KEY를 찾을 수 없습니다.")
    else:
        initialize_database(db_path)
        
        # 2024년 1분기 ~ 2025년 1분기 데이터 수집
        for year in ["2024", "2025"]:
            for quarter in range(1, 5):
                # 2025년은 1분기까지만 존재 -> 종료 조건 설정
                if year == "2025" and quarter > 1:
                    break
                if not update_database_for_period(db_path, api_key, year, str(quarter)): 
                    break
        print("\n--- 모든 데이터 수집 및 업데이트 완료 ---")