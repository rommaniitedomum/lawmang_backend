from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func, ForeignKey
from app.core.database import Base
from datetime import datetime, timedelta

class User(Base):
    """
    SQLAlchemy ORM을 사용하여 users 테이블을 정의
    """
    __tablename__ = "users_account"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)  # 로그인 및 비밀번호 찾기용 이메일
    password_hash = Column(Text, nullable=False)  # 암호화된 비밀번호
    nickname = Column(String(50), unique=True, nullable=False)  # 사용자 닉네임 (중복 방지)
    is_verified = Column(Boolean, default=False)  # 이메일 인증 여부
    created_at = Column(DateTime, server_default=func.now())  # 계정 생성 시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 정보 업데이트 시간

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nickname={self.nickname})>"


class EmailVerification(Base):
    """
    이메일 인증 코드 저장 테이블
    """
    __tablename__ = "email_verifications"

    email = Column(String(255), primary_key=True, unique=True, nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=5))

    def __repr__(self):
        return f"<EmailVerification(email={self.email}, code={self.code}, expires_at={self.expires_at})>"
