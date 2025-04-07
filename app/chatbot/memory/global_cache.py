from typing import Any, Dict, Optional
from langchain.memory import ConversationBufferMemory
import json
import datetime
from langchain.schema import SystemMessage

# LangChain의 메모리 인스턴스 (대화 히스토리 저장용)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def store_template_in_memory(template: dict) -> None:
    # 기존 TEMPLATE_DATA 메시지 제거
    memory.chat_memory.messages = [
        m
        for m in memory.chat_memory.messages
        if not m.content.startswith("TEMPLATE_DATA:")
    ]

    template_json = json.dumps(template, cls=CustomJSONEncoder, ensure_ascii=False)
    message_content = f"TEMPLATE_DATA:{template_json}"
    memory.chat_memory.add_message(SystemMessage(content=message_content))


def retrieve_template_from_memory() -> dict:
    """
    memory에서 저장된 시스템 메시지 중 TEMPLATE_DATA: 로 시작하는 메시지를 찾아
    JSON을 파싱한 후 템플릿 dict를 반환합니다.
    만약 저장된 템플릿이 없다면 빈 dict를 반환합니다.
    """
    for message in memory.chat_memory.messages:
        if message.content.startswith("TEMPLATE_DATA:"):
            template_json = message.content[len("TEMPLATE_DATA:") :]
            return json.loads(template_json)
    return {}
