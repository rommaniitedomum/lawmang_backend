from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# ✅ 메모 생성 스키마
class MemoCreate(BaseModel):
    user_id: int
    title: str
    content: Optional[str] = None
    event_date: Optional[date] = None
    notification: bool = False

# ✅ 메모 수정 스키마
class MemoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    event_date: Optional[date] = None
    notification: Optional[bool] = None

    class Config:
        from_attributes = True

# ✅ 메모 응답 스키마
class MemoResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str]
    event_date: Optional[date]
    notification: bool
    created_at: datetime

    class Config:
        from_attributes = True
        
			
# ✅ 모든 스키마 내보내기
__all__ = [
    'MemoCreate',
    'MemoUpdate',
    'MemoResponse',
]
