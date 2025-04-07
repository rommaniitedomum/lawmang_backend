from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re

# ✅ 회원가입 요청 스키마
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    code: str

    # ✅ 비밀번호 유효성 검사 추가
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('비밀번호는 특수문자를 포함해야 합니다.')
        return v

# ✅ 응답용 사용자 스키마
class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    class Config:
        from_attributes = True

# ✅ 로그인 요청 스키마
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ 이메일 인증 코드 확인을 위한 스키마 추가
class EmailVerificationCreate(BaseModel):
    email: EmailStr
    code: str
    expires_at: datetime