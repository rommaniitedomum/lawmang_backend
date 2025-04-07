from fastapi import APIRouter, Response, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.user_service import (
    create_user, verify_password, create_access_token, send_email_code, save_verification_code, verify_email_code, delete_verification_code, hash_password
)
from app.core.dependencies import get_current_user
import re
from typing import Any

router = APIRouter()


# ✅ 이메일 인증 코드 발송 API (PostgreSQL 저장)
@router.post("/send-code")
def send_verification_code(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="이메일이 필요합니다.")

    # ✅ 이메일 형식 검증
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="유효한 이메일을 입력하세요.")

    # ✅ 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다."
        )

    # ✅ 이메일 인증 코드 발송
    code = send_email_code(email, db)
    save_verification_code(db, email, code, expiry_minutes=5)  # ✅ PostgreSQL에 저장
    return {"message": "이메일로 인증 코드가 전송되었습니다!"}


# ✅ 회원가입 API (이메일 인증 코드 포함, PostgreSQL 사용)
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """회원가입 API (이메일 인증 코드 포함)"""
    
    if not verify_email_code(db, user.email, user.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="잘못된 인증 코드입니다.")

    # ✅ 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 이메일입니다.")

    new_user = create_user(db=db, user=user)

    # ✅ 회원가입 성공 후 인증 코드 삭제
    delete_verification_code(db, user.email)

    return new_user


# ✅ 로그인 API (JWT 토큰 반환)
@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="존재하지 않는 이메일입니다.")

    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비밀번호가 일치하지 않습니다.")

    # ✅ JWT 토큰 생성
    access_token = create_access_token(data={"sub": existing_user.email})

    # 사용자 정보를 포함하여 반환
    response = JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "email": existing_user.email,
            "nickname": existing_user.nickname,
            "id": existing_user.id
        }
    })
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # HTTPS에서만 전송
        samesite='strict',
        max_age=3600  # 1시간
    )
    return response


# ✅ 현재 로그인한 사용자의 이메일로 DB에서 사용자 정보 조회
@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return {
        "email": user.email,
        "nickname": user.nickname,
        "id": user.id
    }


# ✅ 로그아웃 API 추가 (JWT 토큰 무효화)
@router.post("/logout")
def logout_user(response: Response, current_user: dict = Depends(get_current_user)):
    response.delete_cookie(key="access_token")  # ✅ 쿠키에서 JWT 삭제
    return {"message": "로그아웃 성공"}


# ✅ 이메일 인증 코드 확인 엔드포인트 (PostgreSQL 사용)
@router.post("/verify-email")
def verify_email(payload: dict = Body(...), db: Session = Depends(get_db)):
    """이메일 인증 코드 검증 (PostgreSQL 사용)"""
    email = payload.get("email")
    code = payload.get("code")

    if not email or not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이메일과 인증 코드가 필요합니다.")

    if not verify_email_code(db, email, code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="잘못된 인증 코드입니다.")

    return {"message": "이메일 인증이 완료되었습니다!"}


# ✅ 비밀번호 재설정 요청
@router.post("/send-reset-code")
def send_reset_code(payload: dict = Body(...), db: Session = Depends(get_db)):
    """비밀번호 재설정 코드 이메일 발송"""
    email = payload.get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="이메일이 필요합니다.")

    # 사용자 존재 여부 확인
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"exists": False}

    code = send_email_code(email, db)
    return {"exists": True, "message": "비밀번호 재설정 코드가 이메일로 전송되었습니다!"}


# ✅ 인증 코드 확인
@router.post("/verify-reset-code")
def verify_reset_code(payload: dict = Body(...), db: Session = Depends(get_db)):
    """비밀번호 재설정 코드 확인"""
    email = payload.get("email")
    code = payload.get("code")

    if not email or not code:
        raise HTTPException(status_code=400, detail="이메일과 인증 코드가 필요합니다.")

    if not verify_email_code(db, email, code):
        raise HTTPException(status_code=400, detail="잘못된 인증 코드입니다.")

    return {"message": "인증 코드가 확인되었습니다."}


# ✅ 비밀번호 재설정
@router.post("/reset-password")
def reset_password(payload: dict = Body(...), db: Session = Depends(get_db)):
    """비밀번호 재설정"""
    email = payload.get("email")
    code = payload.get("code")
    new_password = payload.get("newPassword")

    if not verify_email_code(db, email, code):
        raise HTTPException(status_code=400, detail="잘못된 인증 코드입니다.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="존재하지 않는 사용자입니다.")

    user.password_hash = hash_password(new_password)
    db.commit()

    delete_verification_code(db, email)
    return {"message": "비밀번호가 성공적으로 변경되었습니다!"}


# ✅ 회원정보 수정 엔드포인트 추가
@router.put("/update")
def update_user(
    payload: dict = Body(...), 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 비밀번호 변경 시에만 현재 비밀번호 확인
    if payload.get("newPassword"):
        if not payload.get("currentPassword"):
            raise HTTPException(status_code=400, detail="현재 비밀번호를 입력해주세요.")
        
        if not verify_password(payload["currentPassword"], user.password_hash):
            raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
        
        user.password_hash = hash_password(payload["newPassword"])

    # 닉네임 업데이트 (비밀번호 확인 없이 가능)
    if "nickname" in payload:
        user.nickname = payload["nickname"]

    db.commit()
    return {"message": "회원정보가 성공적으로 수정되었습니다."}


# ✅ 닉네임 중복 확인 API 추가
@router.get("/auth/check-nickname")
def check_nickname(nickname: str, db: Session = Depends(get_db)):
    """탈퇴한 계정을 제외하고 닉네임 중복 검사"""
    existing_user = db.query(User).filter(
        User.nickname == nickname, 
        User.is_active == True  # ✅ 활성화된 계정만 검색
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")

    return {"message": "사용 가능한 닉네임입니다."}


@router.post("/verify-password")
async def verify_current_password(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if not verify_password(payload.get("currentPassword"), user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid password"
        )
    return {"message": "Password verified"}


# ✅ 회원탈퇴 API
@router.delete("/auth/withdraw", status_code=status.HTTP_200_OK)
async def withdraw_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    # ✅ 회원 데이터 완전 삭제
    db.delete(user)
    db.commit()

    return {"message": "회원탈퇴가 완료되었습니다."}

