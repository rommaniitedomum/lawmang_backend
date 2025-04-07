import asyncio
from typing import List, Optional
from app.chatbot.tool_agents.qualifier import run_consultation_qualifier
from app.chatbot.tool_agents.planner import (
    generate_response_template,
    run_response_strategy_with_limit,
)
from app.chatbot.tool_agents.precedent import LegalPrecedentRetrievalAgent
from app.chatbot.tool_agents.executor.normalanswer import run_final_answer_generation
from app.chatbot.tool_agents.tools import async_search_consultation

# ConversationBufferMemory를 활용한 캐시 함수들 import
from app.chatbot.memory.global_cache import (
    retrieve_template_from_memory,
    store_template_in_memory,
)


async def run_full_consultation(
    user_query: str,
    search_keywords: List[str],
    model: str = "gpt-4",
    build_only: bool = False,
    stop_event: Optional[asyncio.Event] = None,  # ✅ 추가
) -> dict:


    # 캐시 조회: ConversationBufferMemory에서 저장된 TEMPLATE_DATA 메시지 사용
    cached_data = retrieve_template_from_memory()
    if cached_data:

        template = cached_data.get("template")
        strategy = cached_data.get("strategy")
        precedent = cached_data.get("precedent")
        # 빌드 전용 모드면 캐시된 데이터 그대로 반환
        if build_only:
            return {
                "user_query": user_query,
                "template": template,
                "strategy": strategy,
                "precedent": precedent,
                "status": "build_only (cached)",
            }
        # 최종 응답 생성 (캐시된 템플릿 활용)
        final_answer = run_final_answer_generation(
            template=template,
            strategy=strategy,
            precedent=precedent,
            user_query=user_query,
            model=model,
        )

        return {
            "user_query": user_query,
            "template": template,
            "strategy": strategy,
            "precedent": precedent,
            "final_answer": final_answer,
            "status": "ok (cached)",
        }

    # 캐시된 데이터가 없으면 새로 생성
    # 1️⃣ Qualifier 실행
    consultation_results, _, _ = await async_search_consultation(search_keywords)
    if stop_event and stop_event.is_set():

        return {"template": None, "strategy": None, "precedent": None}

    best_case = await run_consultation_qualifier(user_query, consultation_results)
    if not consultation_results:

        return {"template": None, "strategy": None, "precedent": None}
    if not all(k in best_case for k in ["title", "question", "answer"]):

        title = best_case.get("title", "법률상담")
        question = best_case.get("question", user_query)
        answer = best_case.get(
            "answer", "일반적인 법률 정보에 기반하여 응답을 생성합니다."
        )
    else:
        title = best_case["title"]
        question = best_case["question"]
        answer = best_case["answer"]

    if stop_event and stop_event.is_set():

        return {"template": None, "strategy": None, "precedent": None}

    # 2️⃣ Planner - 템플릿 생성
    template = await generate_response_template(title, question, answer, user_query)

    # 3️⃣ 전략 생성
    strategy = await run_response_strategy_with_limit(
        template.get("explanation", ""),  # 🔐 explanation 없을 경우 빈 문자열로 처리
        user_query,
        template.get("hyperlinks", []),
    )

    if stop_event and stop_event.is_set():

        return {"template": None, "strategy": None, "precedent": None}

    # 4️⃣ 판례 검색 등 빌드 완료 후
    precedent_agent = LegalPrecedentRetrievalAgent()
    precedent = await precedent_agent.run(
        categories=[title],
        titles=[title],
        user_input_keywords=search_keywords,
    )

    # 중간 빌드 데이터 구성 (여기에 built 플래그 추가)
    intermediate_data = {
        "template": template,
        "strategy": strategy,
        "precedent": precedent,
        "built": True,  # 기존
        "built_by_llm2": True,  # ✅ 필수: LLM2 생성 템플릿임을 명시
    }
    store_template_in_memory(intermediate_data)


    # 빌드 전용 모드 (GPT 미호출)
    if build_only:
        return {
            "user_query": user_query,
            "template": template,
            "strategy": strategy,
            "precedent": precedent,
            "status": "build_only",
        }

    # 5️⃣ 고급 GPT 응답 생성
    final_answer = run_final_answer_generation(
        template=template,
        strategy=strategy,
        precedent=precedent,
        user_query=user_query,
        model=model,
    )

    return {
        "user_query": user_query,
        "template": template,
        "strategy": strategy,
        "precedent": precedent,
        "final_answer": final_answer,
        "status": "ok",
    }
