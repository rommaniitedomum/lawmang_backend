from fastapi import APIRouter, HTTPException, FastAPI
from pydantic import BaseModel
import os
import sys
import asyncio
from asyncio import Lock, Semaphore
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app.chatbot.tool_agents.executor.normalanswer import run_final_answer_generation
from app.chatbot.initial_agents.controller import run_initial_controller
from app.chatbot.tool_agents.controller import run_full_consultation
from app.chatbot.tool_agents.utils.utils import faiss_kiwi, update_llm2_template_with_es
from app.chatbot.memory.global_cache import retrieve_template_from_memory

# 시스템 환경 설정
sys.path.append(os.path.abspath("."))
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FAISS_PATH = "./app/chatbot_term/vectorstore"

# FastAPI 앱과 Router 정의
app = FastAPI()
router = APIRouter()

# ✅ 전역 리소스
faiss_db = None
llm2_lock = Lock()
llm2_semaphore = Semaphore(2)  # ✅ 최대 2개 동시 실행 제한
yes_count_memory = {}  # YES 카운트 캐시 (세션 확장 가능)


# ✅ 앱 시작 시 FAISS 1회 로딩
@app.on_event("startup")
async def startup_event():
    global faiss_db
    try:
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=OPENAI_API_KEY,
        )
        faiss_db = FAISS.load_local(
            DB_FAISS_PATH,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
        print("✅ FAISS 전역 로딩 완료")
    except Exception as e:
        print(f"❌ FAISS 로딩 실패: {e}")
        faiss_db = None


# ✅ 입력 모델
class QueryRequest(BaseModel):
    query: str


# ✅ 1. LLM1: 초기 응답만
@router.post("/initial")
async def chatbot_initial(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다.")
    if not faiss_db:
        raise HTTPException(status_code=500, detail="FAISS 로드 실패")

    stop_event = asyncio.Event()

    result = await run_initial_controller(
        user_query=user_query,
        faiss_db=faiss_db,
        current_yes_count=0,
        template_data={},
        stop_event=stop_event,
    )

    # ✅ 후처리: LLM2 템플릿이 있으면 ES 기반 업데이트 예약
    cached_template = retrieve_template_from_memory()
    if cached_template and cached_template.get("built_by_llm2"):
        asyncio.create_task(update_llm2_template_with_es(cached_template, user_query))

    return {
        "mcq_question": result.get("mcq_question") or "⚠️ 법률적으로 관계가 없습니다.",
        "yes_count": result.get("yes_count", 0),
        "is_mcq": result.get("is_mcq", True),
    }


# ✅ 2. LLM2 빌드 전용
@router.post("/prepare")
async def chatbot_prepare(request: QueryRequest):
    user_query = request.query.strip()
    if not faiss_db:
        raise HTTPException(status_code=500, detail="FAISS 로드 실패")

    keywords = faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db)
    stop_event = asyncio.Event()

    async with llm2_semaphore:
        await run_full_consultation(
            user_query=user_query,
            search_keywords=keywords,
            model="gpt-4",
            build_only=True,
            stop_event=stop_event,
        )

    return {"status": "ok", "message": "백그라운드 빌드 완료"}


# ✅ 3. LLM2 최종 응답
@router.post("/advanced")
async def chatbot_advanced(request: QueryRequest):
    user_query = request.query.strip()
    if not faiss_db:
        raise HTTPException(status_code=500, detail="FAISS 로드 실패")

    keywords = faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db)
    stop_event = asyncio.Event()

    async with llm2_semaphore:
        prepared_data = await run_full_consultation(
            user_query=user_query,
            search_keywords=keywords,
            model="gpt-4",
            build_only=False,
            stop_event=stop_event,
        )

    if not all(prepared_data.get(k) for k in ["template", "strategy", "precedent"]):
        raise HTTPException(status_code=500, detail="전략 또는 판례 생성 실패")

    async with llm2_lock:
        final_answer = run_final_answer_generation(
            template=prepared_data["template"],
            strategy=prepared_data["strategy"],
            precedent=prepared_data["precedent"],
            user_query=user_query,
            model="gpt-4",
        )

    return {
        "template": prepared_data["template"],
        "strategy": prepared_data["strategy"],
        "precedent": prepared_data["precedent"],
        "final_answer": final_answer,
        "status": "ok",
    }


# ✅ 라우터 등록
app.include_router(router, prefix="/chatbot")
