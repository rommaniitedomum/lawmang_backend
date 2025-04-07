import sys
import os

# 절대 경로로 변경
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

from app.services.memo_service import check_and_send_notifications
from app.core.database import SessionLocal

db = SessionLocal()
sent_count = check_and_send_notifications(db)
print(f"수동 실행 결과: {sent_count}건의 알림이 전송됨")
db.close()