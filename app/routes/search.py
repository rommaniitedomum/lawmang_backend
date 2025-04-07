from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.precedent_service import search_precedents, search_precedents_by_category
from app.services.consultation import search_consultations, search_consultations_by_category

router = APIRouter()

@router.get("/precedents/{keyword}")
def fetch_precedents(keyword: str, db: Session = Depends(get_db)):
    try:
        results = search_precedents(keyword)

        if not results:
            raise HTTPException(status_code=404, detail="검색 결과 없음")  # ✅ FastAPI 기본 예외 처리 활용

        return results  # ✅ FastAPI가 자동으로 JSON 변환

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # ✅ 예외 메시지만 반환

@router.get("/precedents/category/{c_type}")
def fetch_precedents_by_category(c_type: str, db: Session = Depends(get_db)):
    results = search_precedents_by_category(c_type)
    if not results:
        raise HTTPException(status_code=404, detail="검색 결과 없음")
    return results

@router.get("/consultations/{keyword}")
def fetch_consultations(keyword: str, db: Session = Depends(get_db)):
    try:
        results = search_consultations(keyword)

        if not results:
            raise HTTPException(status_code=404, detail="검색 결과 없음")  # ✅ FastAPI 기본 예외 처리 활용

        return results  # ✅ FastAPI가 자동으로 JSON 변환

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # ✅ 예외 메시지만 반환

@router.get("/consultations/category/{category}")
def fetch_consultations_by_category(category: str, db: Session = Depends(get_db)):
    results = search_consultations_by_category(category)
    if not results:
        raise HTTPException(status_code=404, detail="검색 결과 없음")
    return results