from app.core.database import execute_sql
import datetime

def search_precedents(keyword: str):
    """
    키워드를 기반으로 precedent 테이블을 검색하는 함수.
    - '법원' 또는 '지원'이 포함된 단어는 court 컬럼에서 검색.
    - 나머지 단어들은 c_name 컬럼에서 검색.
    - '법원' 키워드가 없으면, c_name, c_number에서 검색.
    """

    # ✅ 키워드 전처리
    keyword = keyword.strip()
    if not keyword:
        return []

    # ✅ 띄어쓰기 제거한 키워드 추가
    no_space_keyword = keyword.replace(" ", "")
    
    tokens = keyword.split()
    court_tokens = [token for token in tokens if "법원" in token or "지원" in token]
    c_name_tokens = [token for token in tokens if token not in court_tokens]

    # ✅ SQL 쿼리 설정
    if court_tokens:
        court_keyword = " ".join(court_tokens)
        if c_name_tokens:
            c_name_keyword = " ".join(c_name_tokens)
            query = """
            SELECT id, c_number, c_type, j_date, pre_number, court, d_link, c_name
            FROM precedent
            WHERE court ILIKE :court_keyword
              AND (
                  c_name ILIKE :c_name_keyword
                  OR REPLACE(c_name, ' ', '') ILIKE :no_space_keyword
              )
            ORDER BY j_date DESC;
            """
            params = {
                "court_keyword": f"%{court_keyword}%",
                "c_name_keyword": f"%{c_name_keyword}%",
                "no_space_keyword": f"%{no_space_keyword}%"
            }
        else:
            query = """
            SELECT id, c_number, c_type, j_date, pre_number, court, d_link, c_name
            FROM precedent
            WHERE court ILIKE :court_keyword
            ORDER BY j_date DESC;
            """
            params = {"court_keyword": f"%{court_keyword}%"}
    else:
        query = """
        SELECT id, c_number, c_type, j_date, pre_number, court, d_link, c_name
        FROM precedent
        WHERE c_name ILIKE :keyword
           OR REPLACE(c_name, ' ', '') ILIKE :no_space_keyword
           OR court ILIKE :keyword
           OR c_number ILIKE :keyword
        ORDER BY j_date DESC;
        """
        params = {
            "keyword": f"%{keyword}%",
            "no_space_keyword": f"%{no_space_keyword}%"
        }

    # ✅ SQL 실행
    results = execute_sql(query, params)

    # ✅ 데이터 변환 (날짜 변환 + 안정성 강화)
    def convert_row(row):
        row_dict = dict(row)
        
        # ✅ j_date가 `None`이면 기본값 처리
        j_date_value = row_dict.get("j_date")
        
        if isinstance(j_date_value, (datetime.date, datetime.datetime)):
            row_dict["j_date"] = j_date_value.isoformat()
        else:
            row_dict["j_date"] = None  # ✅ None 처리하여 JSON 직렬화 오류 방지

        return row_dict

    return [convert_row(row) for row in results]  # ✅ JSON 직렬화 가능하도록 변환

def search_precedents_by_category(c_type: str):
    """
    주어진 c_type(판례 카테고리)에 해당하는 판례 데이터를 검색합니다.
    """
    query = """
    SELECT id, c_number, c_type, j_date, pre_number, court, d_link, c_name
    FROM precedent
    WHERE c_type ILIKE :c_type
    ORDER BY j_date DESC
    LIMIT 80;
    """
    params = {"c_type": f"%{c_type}%"}
    results = execute_sql(query, params)

    def convert_row(row):
        row_dict = dict(row)
        j_date_value = row_dict.get("j_date")
        if isinstance(j_date_value, (datetime.date, datetime.datetime)):
            row_dict["j_date"] = j_date_value.isoformat()
        else:
            row_dict["j_date"] = None
        return row_dict

    return [convert_row(row) for row in results]