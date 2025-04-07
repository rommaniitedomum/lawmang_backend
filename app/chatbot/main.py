import os
import sys
import asyncio
from asyncio import Lock, Event, create_task
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.chatbot.tool_agents.executor.normalanswer import run_final_answer_generation
from app.chatbot.initial_agents.controller import run_initial_controller
from app.chatbot.tool_agents.controller import run_full_consultation
from app.chatbot.tool_agents.utils.utils import faiss_kiwi
from fastapi import FastAPI
from app.chatbot.routes import router as chatbot_router


# ✅ 락: 중복 실행 방지 (LLM2 관련)
llm2_lock = Lock()
yes_count = 0
sys.path.append(os.path.abspath("."))
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_FAISS_PATH = "./app/chatbot_term/vectorstore"
app = FastAPI()

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


async def run_dual_pipeline(user_query: str):
    global yes_count
    # print(f"\n🔍 사용자 질문 수신: {user_query}")

    faiss_db = load_faiss()
    template_data = {}
    if not faiss_db:
        return {"error": "FAISS 로드 실패"}
    stop_event = Event()

    # 1. 초기 응답(LLM1)와 LLM2 빌드 동시 시작
    initial_task = create_task(
        run_initial_controller(
            user_query=user_query,
            faiss_db=faiss_db,
            current_yes_count=yes_count,
            template_data=template_data,
            stop_event=stop_event,
        )
    )
    # LLM2 빌드는 LLM1의 스타트와 동시에 실행 (build_only=True)
    build_task = None
    if not llm2_lock.locked():
        build_task = create_task(
            run_full_consultation(
                user_query,
                faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db),
                model="gpt-4",
                build_only=True,  # 초기 빌드는 build_only 모드로 시작
                stop_event=stop_event,
            )
        )
    else:
        print("⚠️ LLM2 빌드가 이미 진행 중입니다.")

    # 2. 초기 응답(LLM1) 먼저 대기
    initial_result = await initial_task
    status = initial_result.get("status", "ok")
    if status in ["no_triggered", "nonlegal_skipped"] or stop_event.is_set():
        # print(f"🛑 [빌드 중단] status={status} 또는 no감지 → 판례/전략 중단")
        if build_task:
            build_task.cancel()
            try:
                await build_task
            except asyncio.CancelledError:
                print("✅ build_task 정상적으로 취소됨.")
        return {"initial": initial_result, "advanced": None}

    # 업데이트된 YES 카운트
    yes_count = initial_result.get("yes_count", yes_count)

    # 3. 초기 응답에 "###yes" 신호가 있으면(LLM1 신호) 이미 시작된 LLM2 빌드 결과를 기다림
    if "###yes" in initial_result.get("initial_response", "").lower():
        # print("ℹ️ LLM1 신호 감지됨. LLM2 빌드 결과를 기다립니다.")
        # 만약 build_task이 없다면, 새로 full build로 실행 (build_only=False)
        if not build_task:
            build_task = create_task(
                run_full_consultation(
                    user_query,
                    faiss_kiwi.extract_top_keywords_faiss(user_query, faiss_db),
                    model="gpt-4",
                    build_only=False,  # full build 모드
                    stop_event=stop_event,
                )
            )
        # 그렇지 않으면 이미 진행 중인 build_task의 결과를 그대로 기다립니다.

    # 4. LLM2 빌드 결과 대기 (초기 응답과 별개로 진행)
    prepared_data = {}
    if build_task:
        prepared_data = await build_task

    template, strategy, precedent = (
        prepared_data.get("template"),
        prepared_data.get("strategy"),
        prepared_data.get("precedent"),
    )
    if not all([template, strategy, precedent]):
        print("⚠️ 빌드 실패.")
        return {"initial": initial_result, "advanced": None}

    # 5. 고급 응답(LLM2 최종 응답)은 기존 조건(yes_count >= 3) 만족 시에만 생성됨
    advanced_result = None
    if yes_count >= 3:
        async with llm2_lock:
            final_answer = run_final_answer_generation(
                template, strategy, precedent, user_query, "gpt-4"
            )
            yes_count = 1  # YES 카운트 초기화
            advanced_result = {
                "template": template,
                "strategy": strategy,
                "precedent": precedent,
                "final_answer": final_answer,
                "status": "ok",
            }

    return {"initial": initial_result, "advanced": advanced_result}


async def chatbot_loop():
    while True:
        user_query = input("\n❓ 질문을 입력하세요 (종료: exit): ")
        if user_query.lower() == "exit":
            break

        if llm2_lock.locked():
            continue

        result = await run_dual_pipeline(user_query)
        if "error" in result:
            continue

        initial = result["initial"]

        # ✅ 무조건 출력: mcq_question → fallback to initial_response
        mcq = initial.get("mcq_question") or initial.get("initial_response")
        if mcq:
            print(mcq)
        else:
            print("\n없음")

        advanced = result.get("advanced")
        if advanced and advanced.get("final_answer"):
            print("\n🚀 [고급 LLM 응답]:")
            print(
                "📄 템플릿 요약:", advanced.get("template", {}).get("summary", "없음")
            )
            print(
                "🧠 전략 요약:",
                advanced.get("strategy", {}).get("final_strategy_summary", "없음"),
            )
            print("📚 판례 요약:", advanced.get("precedent", {}).get("summary", "없음"))
            print("🔗 링크:", advanced.get("precedent", {}).get("casenote_url", "없음"))
            print("\n🤖 최종 GPT 응답:\n", advanced.get("final_answer", "없음"))
        else:
            print("\n✅ 초기 응답으로 충분합니다.")


app.include_router(chatbot_router, prefix="/api/chatbot")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(chatbot_loop())
    loop.close()


if __name__ == "__main__":
    main()
