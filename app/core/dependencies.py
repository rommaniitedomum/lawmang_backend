from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.services.user_service import verify_access_token
from app.core.config import settings

# ✅ OAuth2 토큰 스키마 정의
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ 현재 로그인한 사용자 가져오기
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return {"sub": email}
    except JWTError:
        raise credentials_exception
