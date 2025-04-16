
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import sys
import asyncio
from asyncio import Lock
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.chatbot.tool_agents.executor.normalanswer import run_final_answer_generation
from app.chatbot.initial_agents.controller import run_initial_controller
from app.chatbot.tool_agents.controller import run_full_consultation
from app.chatbot.tool_agents.utils.utils import faiss_kiwi
from app.chatbot.memory.global_cache import retrieve_template_from_memory, memory
from fastapi import FastAPI
# ✅ 락: 중복 실행 방지 (LLM2 관련)
llm2_lock = Lock()
prepare_lock = Lock()
yes_count = 0
sys.path.append(os.path.abspath("."))
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FAISS_PATH = "./app/chatbot_term/vectorstore"

app = FastAPI()

router = APIRouter()
yes_count_memory = {}  # 간단한 글로벌 YES 메모리 (세션/유저 구분 가능시 확장)


def load_faiss():
    try:
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=OPENAI_API_KEY,
        )
        return FAISS.load_local(
            DB_FAISS_PATH,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
    except Exception as e:
        # print(f"❌ FAISS 로드 실패: {e}")
        return None
class QueryRequest(BaseModel):
    query: str


@router.post("/initial")
async def chatbot_initial(request: QueryRequest):
    user_query = request.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="질문이 비어 있습니다.")

    memory.chat_memory.messages = []
    faiss_db = load_faiss()
    if not faiss_db:
        raise HTTPException(status_code=500, detail="FAISS 로드 실패")

    stop_event = asyncio.Event()
    template_data = {}

    result = await run_initial_controller(
        user_query=user_query,
        faiss_db=faiss_db,
        current_yes_count=0,
        template_data=template_data,
        stop_event=stop_event,
    )

    # ✅ LLM2 캐시된 템플릿이 있다면 포함해서 리턴
    cached_template = retrieve_template_from_memory()
    if cached_template and cached_template.get("built_by_llm2"):
        result["template"] = cached_template.get("template", {})
        result["strategy"] = cached_template.get("strategy", {})
        result["precedent"] = cached_template.get("precedent", {})

    return {
        "mcq_question": result.get("mcq_question") or "⚠️ 법률적으로 관계가 없습니다.",
        "yes_count": result.get("yes_count", 0),
        "is_mcq": result.get("is_mcq", True),
        "template": result.get("template", {}),
        "strategy": result.get("strategy", {}),
        "precedent": result.get("precedent", {}),
    }


# ✅ 2. LLM2 빌드 전용: 전략/판례 캐싱만 수행
@router.post("/prepare")
async def chatbot_prepare(request: QueryRequest):
    async with prepare_lock:
        user_query = request.query.strip()
        faiss_db = load_faiss()
        if not faiss_db:
            raise HTTPException(status_code=500, detail="FAISS 로드 실패")

        keywords = faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db)
        stop_event = asyncio.Event()

        await run_full_consultation(
            user_query=user_query,
            search_keywords=keywords,
            model="gpt-4",
            build_only=True,
            stop_event=stop_event,
        )

        return {"status": "ok", "message": "백그라운드 빌드 완료"}


# ✅ 3. LLM2 최종 응답: 고급 GPT 실행
@router.post("/advanced")
async def chatbot_advanced(request: QueryRequest):
    user_query = request.query.strip()
    faiss_db = load_faiss()
    if not faiss_db:
        raise HTTPException(status_code=500, detail="FAISS 로드 실패")

    keywords = faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db)
    stop_event = asyncio.Event()

    # 전략/판례 + GPT 최종 응답까지 생성
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
