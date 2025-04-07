import os
import random
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.models.user import User
from passlib.context import CryptContext
from app.core.config import settings
from app.models.user import EmailVerification  # ✅ 인증 코드 테이블 추가
from app.schemas.user import UserCreate

# ✅ 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    """비밀번호를 안전하게 해싱하는 함수"""
    return pwd_context.hash(password)

# ✅ 비밀번호 검증 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ✅ JWT 설정
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ✅ JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})  # 만료 시간 추가
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ✅ JWT 토큰 검증 함수
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # {'sub': 'user_email@example.com', 'exp': 1700000000}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

# ✅ 환경 변수 로드 (네이버 SMTP 설정)
load_dotenv()

SMTP_USER = os.getenv("SMTP_USER")  # ✅ 네이버 이메일 계정
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # ✅ SMTP 비밀번호
SMTP_SERVER = os.getenv("SMTP_SERVER")  # ✅ 네이버 SMTP 서버 주소
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # ✅ 기본적으로 587 사용

# ✅ 이메일 인증 코드 생성 및 발송 (PostgreSQL 저장)
def send_email_code(email: str, db: Session) -> str:
    """이메일 인증 코드 생성 및 PostgreSQL에 저장"""
    try:
        code = ''.join(random.choices("0123456789", k=6))
        message = f"회원가입 인증 코드: {code}"

        msg = MIMEText(message)
        msg["Subject"] = "회원가입 인증 코드"
        msg["From"] = SMTP_USER
        msg["To"] = email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, email, msg.as_string())

        print(f"✅ 인증 코드 {code} 이메일 발송 완료: {email}")

        # ✅ PostgreSQL에 인증 코드 저장 (5분 유효)
        save_verification_code(db, email, code, expiry_minutes=5)

        return code

    except smtplib.SMTPAuthenticationError:
        print("❌ 네이버 SMTP 인증 실패: 이메일 또는 비밀번호가 올바르지 않습니다.")
        raise HTTPException(status_code=500, detail="이메일 서버 인증에 실패했습니다.")

    except smtplib.SMTPException as e:
        print(f"❌ 이메일 발송 실패: {e}")
        raise HTTPException(status_code=500, detail="이메일 발송 중 오류가 발생했습니다.")

# ✅ 이메일 인증 코드 저장 (PostgreSQL 사용)
def save_verification_code(db: Session, email: str, code: str, expiry_minutes: int = 5):
    """이메일 인증 코드를 데이터베이스에 저장"""
    expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    verification = db.query(EmailVerification).filter(EmailVerification.email == email).first()
    if verification:
        verification.code = code
        verification.expires_at = expires_at
    else:
        verification = EmailVerification(email=email, code=code, expires_at=expires_at)
        db.add(verification)

    db.commit()

# ✅ 이메일 인증 코드 검증 (PostgreSQL 사용)
def verify_email_code(db: Session, email: str, code: str) -> bool:
    """PostgreSQL에서 이메일 인증 코드 검증"""
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.code == code,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()

    return verification is not None

# ✅ 이메일 인증 코드 삭제 (PostgreSQL 사용)
def delete_verification_code(db: Session, email: str):
    """사용된 인증 코드 삭제"""
    db.query(EmailVerification).filter(EmailVerification.email == email).delete()
    db.commit()

# ✅ 회원 가입 로직 (이메일 인증된 사용자만 가입 가능, PostgreSQL 적용)
def create_user(db: Session, user: UserCreate):
    """PostgreSQL을 사용하여 회원가입"""
    if not verify_email_code(db, user.email, user.code):
        raise HTTPException(status_code=400, detail="잘못된 인증 코드이거나 만료되었습니다.")

    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        nickname=user.nickname,
        is_verified=True  # ✅ 이메일 인증이 완료된 사용자
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ✅ 회원가입 성공 후 PostgreSQL에서 인증 코드 삭제
    delete_verification_code(db, user.email)

    return new_user
