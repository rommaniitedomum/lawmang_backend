from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# 활동 기록(History) 생성 스키마
class HistoryCreate(BaseModel):
    user_id: int
    consultation_id: Optional[int] = None
    precedent_id: Optional[int] = None
    activity_type: str
    created_at: datetime = Field(default_factory=datetime.now)

# 활동 기록(History) 응답 스키마
class HistoryResponse(HistoryCreate):
    id: int

    class Config:
        from_attributes = True

# 열람 기록(History) 생성 스키마
class HistoryViewedCreate(BaseModel):
    consultation_id: Optional[int] = None
    precedent_id: Optional[int] = None

# 열람 기록(History) 응답 스키마
class HistoryViewedResponse(BaseModel):
    id: int
    user_id: int
    consultation_id: Optional[int] = None
    precedent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

__all__ = [
    'HistoryCreate',
    'HistoryResponse',
    'HistoryViewedCreate',
    'HistoryViewedResponse'
]
