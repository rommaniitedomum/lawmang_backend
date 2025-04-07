import os
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def load_llm():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=OPENAI_API_KEY,
        temperature=0.6,
        max_tokens=256,
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

        다음 정보를 바탕으로 판단하세요:

        💬 대화 기록:
        {chat_history}

        ❓ 사용자 질문:
        "{user_query}"

        🧠 사용자 입력 키워드:
        {query_keywords}

        📚 FAISS 유사 키워드:
        {faiss_keywords}

        📂 질문 유형:
        {query_type}

        📄 유사 상담 검색 결과 (Elasticsearch 기반):
        {es_context}

        📢 지시사항:
        - 아래 형식에 따라 실시간 판단 보고서를 작성하세요.
        - 단, 지금은 상세한 문장이 주어지지 않습니다.
        - 먼저 천천히 생각해서 보고서 항목 중 0, 1, 2, 4 번 항목을 유추하기에 가장 중요한 단어 5개로 전달하세요.
        - 0, 1, 2, 4 번 항목 예시 =  계약, 해지, 통보, 위약금, 문제
        - 3번은 숫자로만 나타내세요
        - 단어 간 연관성과 법률적 가능성을 바탕으로, 최대한 논리적으로 작성하세요.
        - 질문이 법률적이지 않거나 너무 모호하면 반드시 `###no`로 끝내세요.

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
        - 법률 관련성 (0~5):
        - 정보 완전성 (0~5):
        - 총점 (합산):

        4. 📋 중간 요약:
        - 법률적으로 대응 가능한 핵심 방향을 5단어료 표현하세요

        마지막 줄에 판단 결과 기입:  
        ###yes 또는 ###no
        -----------------------------
        """,
            input_variables=[
                "chat_history",
                "user_query",
                "query_keywords",
                "faiss_keywords",
                "query_type",
                "es_context",
            ],
        )

    async def build_es_context(self, user_query: str) -> str:
        # ✅ ES 결과 없으면 직접 검색
        es_results = await async_ES_search_one([user_query])

        if not es_results:
            return "관련 상담사례가 없습니다."

        es_context = ""
        for i, item in enumerate(es_results[:1], start=1):  # 상위 3개만
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
        query_keywords = faiss_kiwi.extract_keywords(user_query, top_k=5)
        faiss_keywords = faiss_kiwi.extract_top_keywords_faiss(
            user_query, self.faiss_db, top_k=5
        )
        legal_score = sum(1 for kw in query_keywords if kw in faiss_keywords) / max(
            len(query_keywords), 1
        )
        query_type = classify_legal_query(user_query, set(faiss_keywords))
        chat_history = self.memory.load_memory_variables({}).get("chat_history", "")

        # ✅ ES 유사 상담 내용 추출
        es_context = await self.build_es_context(user_query)

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

        full_response = ""
        is_no_detected = False

        async for chunk in self.llm.astream(prompt):
            content = getattr(chunk, "content", str(chunk))
            if content:
                sys.stdout.write(content)
                sys.stdout.flush()
                full_response += content

                # 실시간 감지
                if "###no" in full_response[-10:].lower():
                    is_no_detected = True
                    if stop_event:
                        stop_event.set()
                    break

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
