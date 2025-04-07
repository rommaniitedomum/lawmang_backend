from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# ✅ SQLAlchemy 엔진 생성 (커넥션 풀 설정 추가)
engine = create_engine(
    DATABASE_URL,
    pool_size=10,       # 최대 10개의 커넥션 유지
    max_overflow=20,    # 최대 20개까지 추가 가능
    pool_timeout=30,    # 30초 동안 연결을 기다림
    pool_recycle=1800   # 30분마다 커넥션 재사용
)

# ✅ ORM을 위한 세션 팩토리 (유저 관리용)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ ORM 모델을 위한 베이스 클래스
Base = declarative_base()

# ✅ ORM 세션을 제공하는 함수 (예외 발생 시 롤백 추가)
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()  # ✅ 예외 발생 시 롤백
        raise e
    finally:
        db.close()

# ✅ SQL 직접 실행을 위한 함수 (SQL Injection 방지 + 오류 처리)
def execute_sql(query: str, params: dict | None = None, fetch_one: bool = False):
    """
    SQL 쿼리를 안전하게 실행하고 결과를 반환하는 함수.
    ORM이 필요하지 않은 판례 및 법률 데이터 조회에 사용.
    오류 발생 시 빈 리스트를 반환합니다.
    
    :param query: 실행할 SQL 쿼리
    :param params: SQL 파라미터 딕셔너리
    :param fetch_one: 단일 행 반환 여부 (기본값: False)
    :return: 딕셔너리 형태의 결과 또는 리스트
    """
    if params is None:
        params = {}

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            mapped_result = result.mappings().all()  # ✅ 딕셔너리 형태로 반환

            if fetch_one:
                return mapped_result[0] if mapped_result else None  # ✅ 단일 결과 반환

            return mapped_result  # ✅ 여러 개 결과 반환
    except SQLAlchemyError as e:
        print(f"SQL 실행 중 오류 발생: {e}")  # 로깅 추가 가능
        return None if fetch_one else []

# ✅ 테이블 자동 생성 함수 (중복 생성 방지)
def init_db():
    from app.models.user import User, EmailVerification
    inspector = inspect(engine)
    
    # 테이블이 존재하지 않는 경우에만 생성
    if not inspector.has_table('users') and not inspector.has_table('email_verifications'):
        Base.metadata.create_all(bind=engine)
        print("테이블이 성공적으로 생성되었습니다.")   

# 직접 실행을 위한 코드 추가
if __name__ == "__main__":
    init_db()
