from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core import get_db

router = APIRouter()

@router.get("/database")
def check_db(db:Session = Depends(get_db)):
  try:
    db.execute(text("SELECT 1"))
    return {"status": "DB 연결 성공!"}
  except Exception as e:
    return {"status": "DB 연결 실패", "error": str(e)}