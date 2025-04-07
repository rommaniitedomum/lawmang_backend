# app/services/consultation_service.py
from app.core.database import execute_sql

def get_consultation_detail_by_id(consultation_id: int):
    """
    주어진 consultation_id에 해당하는 legal_consultation 테이블의 상세 정보를 조회합니다.
    
    Args:
        consultation_id (int): 상세 정보를 조회할 상담 사례의 고유 ID.
    
    Returns:
        dict: 해당 상담 사례의 상세 정보가 담긴 딕셔너리. 
              결과가 없으면 None을 반환합니다. 
    """
    query = """
        SELECT id, category, sub_category, title, question, answer
        FROM legal_consultation
        WHERE id = :consultation_id;
    """
    params = {"consultation_id": consultation_id}
    results = execute_sql(query, params)
    
    # 결과가 있으면 첫 번째 행을 dict로 변환하여 반환
    if results:
        return dict(results[0])
    return None
