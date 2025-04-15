# ✅ controller.py
import asyncio
from typing import Dict, Optional
from langchain_community.vectorstores import FAISS
from app.chatbot.initial_agents.initial_chatbot import LegalChatbot
from app.chatbot.initial_agents.ask_human_for_info import AskHumanAgent
async def run_initial_controller(
    user_query: str,
    faiss_db: FAISS,
    current_yes_count: int = 0,
    template_data: Optional[Dict[str, any]] = None,
    stop_event: Optional[asyncio.Event] = None,
) -> Dict:
    chatbot = LegalChatbot(faiss_db=faiss_db)
    ask_human_agent = AskHumanAgent()

    # ✅ 병렬 실행: LLM1 + 템플릿 선 생성
    chatbot_task = asyncio.create_task(
        chatbot.generate(
            user_query=user_query,
            current_yes_count=current_yes_count,
            stop_event=stop_event,
        )
    )
    # ask_human_task = asyncio.create_task(
    #     ask_human_agent.ask_human(
    #         user_query=user_query,
    #         llm1_answer=None,
    #         current_yes_count=current_yes_count,
    #         template_data=None,
    #         initial_response=None,
    #     )
    # )

    # ✅ LLM1 먼저 기다림
    initial_result = await chatbot_task
    initial_response = initial_result.get("initial_response", "")
    is_no = initial_result.get("is_no", False)
    query_type = initial_result.get("query_type", "legal")
    updated_yes_count = initial_result.get("yes_count", current_yes_count)
    escalate_directly = initial_result.get("escalate_to_advanced", False)

    if is_no and stop_event:
        # print("🛑 [controller] is_no=True → stop_event.set() 실행됨")
        stop_event.set()

    # ✅ ask_human 재호출 (LLM1 응답 기반 판단)
    try:
        ask_result = await asyncio.wait_for(
            ask_human_agent.ask_human(
                user_query=user_query,
                llm1_answer=initial_response,
                current_yes_count=updated_yes_count,
                template_data=None,
                initial_response=None,
            ),
            timeout=8.0,  # 혹시 오래 걸릴 경우 방지
        )
        # print("✅ [controller] ask_human 반환 성공:", ask_result)
    except asyncio.TimeoutError:
        # print("⏱️ [controller] ask_human 타임아웃 발생")
        ask_result = {
            "yes_count": updated_yes_count,
            "mcq_question": "⏳ 템플릿 응답이 지연되고 있습니다.",
            "is_mcq": False,
            "load_template_signal": False,
            "template": {},
        }

    final_yes_count = ask_result.get("yes_count", updated_yes_count)
    escalate_to_advanced = escalate_directly or final_yes_count >= 3

    if query_type == "nonlegal":
        return {
            "status": "nonlegal_skipped",
            "initial_response": initial_response,
        }

    status = "ok"
    if escalate_to_advanced:
        status = "advanced_triggered"
    elif ask_result.get("load_template_signal"):
        status = "template_load_triggered"
    elif is_no:
        status = "no_triggered"

    return {
        "initial_response": initial_response,
        "escalate_to_advanced": escalate_to_advanced,
        "yes_count": final_yes_count,
        "load_template_signal": ask_result.get("load_template_signal"),
        "status": status,
        "mcq_question": ask_result.get("mcq_question"),
        "is_mcq": ask_result.get("is_mcq"),
        "template": ask_result.get("template"),
    }
