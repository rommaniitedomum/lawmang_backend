from sqlalchemy import Column, Integer, DateTime, Index, func, CheckConstraint
from app.core.database import Base

class History(Base):
    """
    사용자의 상담 사례 및 판례 열람 기록을 저장하는 테이블
    """
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)  # 외래 키 없이 관리
    consultation_id = Column(Integer, nullable=True)  # 상담 사례 ID
    precedent_id = Column(Integer, nullable=True)  # 판례 ID
    created_at = Column(DateTime, default=func.now())  # 생성 시간

    __table_args__ = (
        # consultation_id와 precedent_id 중 하나는 반드시 있어야 함
        CheckConstraint(
            'consultation_id IS NOT NULL OR precedent_id IS NOT NULL',
            name='check_consultation_or_precedent_not_both_null'
        ),
        # user_id와 (consultation_id 또는 precedent_id)가 동일할 경우 중복 기록을 방지
        Index(
            'unique_user_consultation_precedent_idx',
            'user_id',
            func.coalesce(consultation_id, -1),
            func.coalesce(precedent_id, -1),
            unique=True
        ),
    )
