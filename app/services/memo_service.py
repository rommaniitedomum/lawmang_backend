import pytz
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models.memo import Memo
from app.schemas.memo import MemoUpdate


# ✅ 메모리 캐시 추가 (전역 변수)
_view_cache = {}
CACHE_DURATION = 60  # 캐시 유효 시간 (초)

# ✅ 메모 저장
def create(db: Session, user_id: int, title: str, content: str = None, 
           event_date = None, notification: bool = False):
    try:
        if event_date and isinstance(event_date, str):
            event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        new_memo = Memo(
            user_id=user_id,
            title=title,
            content=content,
            event_date=event_date,
            notification=notification
        )
        db.add(new_memo)
        db.commit()
        db.refresh(new_memo)
        return new_memo
    except SQLAlchemyError as e:
        print(f"🔥 메모 저장 오류: {e}")
        db.rollback()
        return None


# ✅ 사용자 메모 조회
def get_list(db: Session, user_id: int):
    return db.query(Memo).filter(
        Memo.user_id == user_id
    ).order_by(Memo.created_at.desc()).all()


# ✅ 메모 수정
def update(db: Session, memo_id: int, user_id: int, memo_data: MemoUpdate):
    try:
        memo = db.query(Memo).filter(
            Memo.id == memo_id,
            Memo.user_id == user_id
        ).first()

        if not memo:
            return None

        for field, value in memo_data.dict(exclude_unset=True).items():
            setattr(memo, field, value)

        db.commit()
        db.refresh(memo)
        return memo
    except SQLAlchemyError as e:
        print(f"🔥 메모 업데이트 오류: {e}")
        db.rollback()
        return None


# ✅ 캐시 정리 함수 추가
def cleanup_cache():
    current_time = datetime.utcnow()
    expired_keys = [
        key for key, (timestamp, _) in _view_cache.items()
        if (current_time - timestamp).total_seconds() > CACHE_DURATION
    ]
    for key in expired_keys:
        del _view_cache[key]


# ✅ 메모 삭제
def remove(db: Session, memo_id: int, user_id: int):
    try:
        memo = db.query(Memo).filter(
            Memo.id == memo_id,
            Memo.user_id == user_id
        ).first()

        if not memo:
            return False

        db.delete(memo)
        db.commit()
        return True
    except SQLAlchemyError as e:
        print(f"🔥 메모 삭제 오류: {e}")
        db.rollback()
        return False


# ✅ 알림 전송 프로세스
def check_and_send_notifications(db: Session):
    local_tz = pytz.timezone("Asia/Seoul")
    now_local = datetime.now(local_tz)
    today = now_local.date()

    print(f"[DEBUG] 현재 로컬 시간: {now_local} (오늘 날짜: {today})")

    memos_to_notify = db.query(Memo).filter(
        Memo.notification == True,
        Memo.event_date != None,
        func.date(Memo.event_date) == today
    ).all()

    print(f"[DEBUG] 조건에 맞는 메모 수: {len(memos_to_notify)}")
    
    sent_count = 0
    for memo in memos_to_notify:
        print(f"[DEBUG] 전송 시도: 메모 ID {memo.id}, event_date: {memo.event_date}, user_id: {memo.user_id}")

        if send_memo_notification_email(db, memo):
            sent_count += 1
        else:
            print(f"[ERROR] 메모 ID {memo.id} 이메일 전송 실패")

    print(f"[INFO] 총 전송 성공 건수: {sent_count}")


# ✅ 메모 알림 이메일 전송
def send_memo_notification_email(db: Session, memo):
    from app.models.user import User
    user = db.query(User).filter(User.id == memo.user_id).first()

    if not user:
        print(f"[ERROR] 사용자 ID {memo.user_id} 정보 없음")
        return False

    if not user.email:
        print(f"[ERROR] 사용자 ID {memo.user_id} 이메일 없음")
        return False

    print(f"[INFO] {user.email}로 메모 알림 전송 시도 중...")

    try:
        from app.services.user_service import SMTP_USER, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
        from email.mime.text import MIMEText
        import smtplib

        msg = MIMEText(f"메모 '{memo.title}'에 대한 알림입니다.\n내용: {memo.content}")
        msg["Subject"] = f"[Memo 알림] {memo.title}"
        msg["From"] = SMTP_USER
        msg["To"] = user.email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, user.email, msg.as_string())

        print(f"[SUCCESS] {user.email}로 메모 알림 이메일 전송 완료")
        return True

    except smtplib.SMTPException as e:
        print(f"[ERROR] 이메일 전송 실패: {e}")
        return False


# ✅ 알림 상태 수정
def update_alert(db: Session, memo_id: int, user_id: int, notification: bool):
    try:
        memo = db.query(Memo).filter(
            Memo.id == memo_id,
            Memo.user_id == user_id
        ).first()

        if not memo:
            return False

        memo.notification = notification
        db.commit()
        return True
    except SQLAlchemyError as e:
        print(f"🔥 알림 설정 업데이트 오류: {e}")
        db.rollback()
        return False