import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# ✅ .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # ✅ 데이터베이스 설정
    DB_HOST: str = os.getenv("DB_HOST")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_PORT: str = os.getenv("DB_PORT", "5432")  # 기본값 5432 설정

    # ✅ JWT 시크릿 키
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")  # 기본값 설정
    ALGORITHM: str = "HS256"  # 기본 알고리즘
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # JWT 만료 시간 (30분)

    # ✅ SQLAlchemy에서 사용할 데이터베이스 URL 생성
    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # 법률상담 챗봇
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY")
    

# ✅ 설정 객체 생성
settings = Settings()

# ✅ 다른 모듈에서 사용할 변수들을 명시적으로 export
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 누락된 export 추가 필요
DB_HOST = settings.DB_HOST
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_PORT = settings.DB_PORT

# 법률상담 챗봇
OPENAI_API_KEY = settings.OPENAI_API_KEY
TAVILY_API_KEY = settings.TAVILY_API_KEY

# ✅ 개발 모드에서만 DB URL 출력 (보안 강화)
if os.getenv("ENV") == "development":
    print("DATABASE_URL:", DATABASE_URL)  # 🚀 개발 모드에서만 출력
