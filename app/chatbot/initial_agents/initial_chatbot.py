import os
import asyncio
import sys
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from asyncio import Event

from app.chatbot.tool_agents.utils.utils import (
    faiss_kiwi,
    classify_legal_query,
)
from app.chatbot.tool_agents.tools import async_ES_search_one

load_dotenv()
OPENAI_API_KEY2 = os.getenv("OPENAI_API_KEY2")


def load_llm():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=OPENAI_API_KEY2,
        temperature=0.1,
        max_tokens=1024,
        streaming=False,
    )


class LegalChatbot:
    def __init__(self, faiss_db):
        self.llm = load_llm()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        self.faiss_db = faiss_db
        self.prompt_template = PromptTemplate(
            template="""
        당신은 대한민국의 법률 전문가입니다.  
        현재 사용자의 질문에 대한 **법률적 타당성, 정보의 명확성, 유사 사례와의 적합성**을 기준으로  
        '실시간 보고서' 형태로 평가해 주세요.
        
            📄 유사 상담 검색 결과 (Elasticsearch 기반/ ):
        {es_context}

        다음 정보를 바탕으로 판단하세요:

        ❓ 사용자 질문:
        "{user_query}"


📢 지시사항:

- 모든 판단은 **사용자 질문의 핵심 키워드**를 기준으로 삼아야 하며, **Elasticsearch 검색 결과는 참고용**입니다.
- 질문과 ES 결과의 **주제가 명백히 다르면 ES는 무시**하십시오.  
  예: 질문이 ‘판사의 감정기복’인데 ES는 ‘보행자’ 관련일 경우 → ES 무시.

✅ [판단 공식]:

1. 다음 항목들의 합산 점수를 계산하세요:
   - 질문 명확성 (0~5)
   - 법률 관련성 (0~5)
   - 정보 완전성 (0~5)
   - [보너스] ES 검색 타이틀과 사용자 질문의 **주제 유사성 점수** (0~5)

2. **총점 14점 이상일 경우 → `###yes`**  
   **총점 13점 이하일 경우 → `###no`**

📌 주의:
- ES의 주제가 겉보기엔 비슷해 보여도 **핵심 키워드가 완전히 다르면 점수를 0점으로 간주**하십시오.
- 특히 질문이 짧더라도 실재 법률 용어나 주제가 포함된 경우, 적극적으로 ###yes 판단이 가능함.
- **매우 비법률적이라 판단되는 용어들은 지체없으 ###no 를 출력하세요.**

🧠 작성 형식:
- 각 항목은 **명사형 키워드 5개**로 표현
- 마지막 줄에 반드시 `###yes` 또는 `###no`로 종료



-----------------------------

        📌 [실시간 판단 보고서]

        0. 🔎 사용자 질문 자체의 법률성 판단:
        - 질문 자체가 법적으로 유의미한가? 명확하고 구체적인가? 5단어 표현

        1. 📍 제목:
        - 본 질문에 적합한 상담 제목을 5단어로 표현하세요.

        2. 👥 사용자 상황과 유사한가?
        - 유사한 상황이 존재할 수 있다고 판단되는걸 5단어로 표현하세요

        3. 📝 평가 점수:
        - 질문 명확성 (0~5):  
        ※ 질문이 짧더라도 법률 키워드가 명확하면 3점 이상 부여  
        - 법률 관련성 (0~5):  
        - 정보 완전성 (0~5):  
        ※ 세부 내용이 부족하더라도 일반 법률 영역에 귀속 가능하면 2점 이상 부여  
        - 총점 (합산):

        4. 📋 중간 요약:
        - 법률적으로 대응 가능한 핵심 방향을 5단어료 표현하세요

        마지막 줄에 판단 결과 기입:  
        ###yes 또는 ###no
-----------------------------
        """,
            input_variables=[
                "user_query",
                "es_context",
            ],
        )

    async def build_es_context(self, user_query: str) -> str:
        es_results = await async_ES_search_one([user_query])

        max_score = es_results.get("max_score", 0)
        hits = es_results.get("hits", [])

        if not hits or max_score < 20:
            return "관련 상담사례가 없습니다."

        es_context = ""
        for i, item in enumerate(hits[:1], start=1):  # 상위 1개만 사용
            es_context += f"\n📌 [{i}번 상담]\n"
            es_context += f"- 제목(title): {item.get('title', '')}\n"
            es_context += f"- 질문(question): {item.get('question', '')}\n"
            es_context += f"- 답변(answer): {item.get('answer', '')}\n"

        return es_context.strip()

    async def generate(
        self,
        user_query: str,
        current_yes_count: int = 0,
        stop_event: Event = None,
    ):
        # print("🔍 [1] ES 사전 검색(prefetch) 시작")
        es_task = asyncio.create_task(self.build_es_context(user_query))

        # print("🧠 [2] 키워드 추출 및 쿼리 분석")
        query_keywords = faiss_kiwi.extract_keywords(user_query, top_k=5)
        faiss_keywords = faiss_kiwi.extract_top_keywords_faiss(
            user_query, self.faiss_db, top_k=5
        )
        legal_score = sum(1 for kw in query_keywords if kw in faiss_keywords) / max(
            len(query_keywords), 1
        )
        query_type = classify_legal_query(user_query, set(faiss_keywords))
        chat_history = self.memory.load_memory_variables({}).get("chat_history", "")

        # print("⏳ [3] ES 검색 결과 대기")
        es_context = await es_task
        # print("✅ [4] ES context 확보 완료")

        # ✅ 프롬프트 구성
        prompt = self.prompt_template.format(
            chat_history=chat_history,
            user_query=user_query,
            query_keywords=", ".join(query_keywords),
            faiss_keywords=", ".join(faiss_keywords),
            legal_score=f"{legal_score:.2f}",
            query_type=query_type,
            es_context=es_context,
        )

        # print("💬 [5] LLM 응답 생성 시작")
        response = await self.llm.ainvoke(prompt)
        full_response = response.content.strip()

        is_no_detected = "###no" in full_response.lower()
        if is_no_detected and stop_event:
            stop_event.set()

        # print("💾 [6] 메모리 저장 및 결과 반환")
        self.memory.save_context(
            {"user_query": user_query}, {"response": full_response}
        )

        return {
            "initial_response": full_response,
            "escalate_to_advanced": False,
            "yes_count": current_yes_count,
            "query_type": query_type,
            "is_no": is_no_detected,
        }