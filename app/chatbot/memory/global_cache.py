# ✅ app/chatbot/memory/global_cache.py

from typing import Dict
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
import json
import datetime

# ✅ 싱글톤 메모리 인스턴스
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# ✅ 날짜 처리 가능한 JSON 인코더
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


# ✅ 템플릿 저장
def store_template_in_memory(template: dict) -> None:
    if not isinstance(template, dict) or "template" not in template:
        raise ValueError("❌ 유효하지 않은 템플릿 구조입니다.")

    # 기존 TEMPLATE_DATA 제거
    memory.chat_memory.messages = [
        m
        for m in memory.chat_memory.messages
        if not m.content.startswith("TEMPLATE_DATA:")
    ]

    template_json = json.dumps(template, cls=CustomJSONEncoder, ensure_ascii=False)
    message_content = f"TEMPLATE_DATA:{template_json}"
    memory.chat_memory.add_message(SystemMessage(content=message_content))


# ✅ 템플릿 조회
def retrieve_template_from_memory() -> dict:
    for message in memory.chat_memory.messages:
        if message.content.startswith("TEMPLATE_DATA:"):
            template_json = message.content[len("TEMPLATE_DATA:") :]
            try:
                return json.loads(template_json)
            except json.JSONDecodeError:
                return {}
    return {}


# ✅ 템플릿 초기화 (선택)
def clear_template_from_memory() -> None:
    memory.chat_memory.messages = [
        m
        for m in memory.chat_memory.messages
        if not m.content.startswith("TEMPLATE_DATA:")
    ]
