from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.history_service import (
    create_viewed as create_viewed_service,
    get_user_viewed,
    remove_viewed,
    remove_all_viewed,
    get_precedent_detail
)
from app.schemas.history import (
    HistoryViewedCreate, HistoryViewedResponse
)

router = APIRouter()

# ✅ 열람 기록 생성
@router.post("/{user_id}", response_model=HistoryViewedResponse)
def create_viewed_log(
    user_id: int, 
    history: HistoryViewedCreate, 
    db: Session = Depends(get_db)
):
    try:
        print(f"Received data: user_id={user_id}, history={history}")  # 디버깅용
        result = create_viewed_service(
            db=db,
            user_id=user_id,
            consultation_id=history.consultation_id,
            precedent_id=history.precedent_id
        )
        return result
    except ValueError as e:
        print(f"Error creating history: {e}")  # 디버깅용
        raise HTTPException(status_code=400, detail=str(e))


# ✅ 사용자의 열람 기록 조회
@router.get("/{user_id}", response_model=list[HistoryViewedResponse])
def get_viewed(user_id: int, db: Session = Depends(get_db)):
    histories = get_user_viewed(db, user_id)
    if not histories:
        return []  # 404 대신 빈 배열 반환
    return histories


# ✅ 열람 기록 삭제
@router.delete("/{history_id}")
def delete_viewed(history_id: int, db: Session = Depends(get_db)):
    success = remove_viewed(db, history_id)
    if not success:
        raise HTTPException(status_code=404, detail="열람 기록을 찾을 수 없습니다.")
    return {"message": "열람 기록이 삭제되었습니다.", "history_id": history_id}


# ✅ 사용자의 모든 열람 기록 삭제
@router.delete("/user/{user_id}")
def delete_all_viewed(user_id: int, db: Session = Depends(get_db)):
    success = remove_all_viewed(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 열람 기록이 없습니다.")
    return {"message": "모든 열람 기록이 삭제되었습니다.", "user_id": user_id}


# ✅ 열람 목록에서 판례 정보를 조회하는 API
@router.get("/precedent-info/{precedent_id}")
def get_precedent_data(precedent_id: int):
    """
    판례 번호를 기반으로 판례 정보를 조회하는 엔드포인트
    """
    precedent_info = get_precedent_detail(precedent_id)

    if not precedent_info:
        return {"error": "해당 판례 정보를 찾을 수 없습니다."}

    return precedent_info