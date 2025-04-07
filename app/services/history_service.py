from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.history import History
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from functools import lru_cache
from app.core.database import execute_sql


# ✅ 열람 기록 저장
def create_viewed(db: Session, user_id: int, consultation_id=None, precedent_id=None):
    """
    열람 기록 생성 함수 (유니크 제약조건으로 중복 방지)
    """
    try:
        # ✅ 새 기록 생성 시도
        new_history = History(
            user_id=user_id,
            consultation_id=consultation_id,
            precedent_id=precedent_id
        )
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        print(f"Created new record: user_id={user_id}, consultation_id={consultation_id}, precedent_id={precedent_id}")
        return new_history

    except IntegrityError:
        # ✅ 중복으로 인한 에러 발생 시 기존 기록 반환
        db.rollback()
        existing_record = db.query(History).filter(
            and_(
                History.user_id == user_id,
                History.consultation_id == consultation_id,
                History.precedent_id == precedent_id
            )
        ).first()
        print(f"Found existing record: user_id={user_id}, consultation_id={consultation_id}, precedent_id={precedent_id}")
        return existing_record

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        db.rollback()
        raise ValueError(f"열람 기록 생성 중 오류 발생: {str(e)}")


# ✅ 사용자의 열람 기록 조회
@lru_cache(maxsize=128)
def get_user_viewed(db: Session, user_id: int):
    """
    사용자의 열람 기록 조회 함수
    """
    return db.query(History).filter(
        History.user_id == user_id
    ).all()


# ✅ 특정 열람 기록 삭제
def remove_viewed(db: Session, history_id: int):
    """
    특정 열람 기록 삭제 함수
    """
    try:
        history = db.query(History).filter(
            History.id == history_id
        ).first()

        if not history:
            return False

        db.delete(history)
        db.commit()
        return True
    except SQLAlchemyError as e:
        print(f"🔥 열람 기록 삭제 오류: {e}")
        db.rollback()
        return False


# ✅ 사용자의 모든 열람 기록 삭제
def remove_all_viewed(db: Session, user_id: int):
    """
    사용자의 모든 열람 기록 삭제 함수
    """
    try:
        histories = db.query(History).filter(
            History.user_id == user_id
        ).all()
        
        if not histories:
            return False

        for history in histories:
            db.delete(history)
        
        db.commit()
        return True
    except SQLAlchemyError as e:
        print(f"🔥 전체 열람 기록 삭제 오류: {e}")
        db.rollback()
        return False


# ✅ 열람기록 판례 목록 정보 불러오기
def get_precedent_detail(precedent_id: int):
    """
    판례 정보 조회 함수
    """
    sql = """
        SELECT c_name, c_number, court, j_date 
        FROM precedent 
        WHERE pre_number = :precedent_id
    """
    result = execute_sql(sql, {"precedent_id": precedent_id}, fetch_one=True)

    if not result:
        print(f"판례 정보를 찾을 수 없음: precedent_id={precedent_id}")
        return None

    return {
        "title": result["c_name"],
        "caseNumber": result["c_number"],
        "court": result["court"],
        "date": result["j_date"],
    }