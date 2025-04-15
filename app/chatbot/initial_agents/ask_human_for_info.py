import os
import json
import asyncio
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from app.chatbot.tool_agents.tools import LawGoKRTavilySearch, async_ES_search_one
from app.chatbot.tool_agents.utils.utils import (
    insert_hyperlinks_into_text,
    evalandsave_llm2_template_with_es,
    calculate_llm2_accuracy_score,
)
# 글로벌 캐시 기능: 템플릿을 시스템 메시지로 저장하고 조회하는 함수들
from app.chatbot.memory.global_cache import (
    retrieve_template_from_memory,store_template_in_memory
)
from app.chatbot.initial_agents.prompt_tone_selector import get_prompt_by_score
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def load_llm():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=OPENAI_API_KEY,
        temperature=0.3,
        max_tokens=2048,
    )


class AskHumanAgent:
    def __init__(self):
        self.llm = load_llm()
        self.tavily_search = LawGoKRTavilySearch()

    async def build_mcq_prompt_full(
        self,
        user_query,
        llm1_answer,
        template_data,
        yes_count,
        report: Optional[str] = None,
        max_score: Optional[float] = None,
        tone_prompt: Optional[str] = None,
    ):
        template = template_data.get("template", {})
        strategy = template_data.get("strategy", {})
        precedent = template_data.get("precedent", {})

        summary_with_links = insert_hyperlinks_into_text(
            template.get("summary", ""), template.get("hyperlinks", [])
        )
        explanation_with_links = insert_hyperlinks_into_text(
            template.get("explanation", ""), template.get("hyperlinks", [])
        )
        hyperlinks_text = "\n".join(
            f"- {link['label']}: {link['url']}" for link in template.get("hyperlinks", [])
        )
        strategy_decision_tree = "\n".join(strategy.get("decision_tree", []))
        precedent_summary = precedent.get("summary", "판례 요약 없음")
        precedent_link = precedent.get("casenote_url", "링크 없음")
        precedent_meta = f"{precedent.get('court', '')} / {precedent.get('j_date', '')} / {precedent.get('title', '')}"

        # ✅ 정확도 기반 프롬프트 톤 조절
        accuracy = template_data.get("llm2_accuracy_score", 0)
        prompt = get_prompt_by_score(
            max_score=accuracy,  # ✅ 여기 반영
            user_query=user_query,
            summary_with_links=summary_with_links,
            explanation_with_links=explanation_with_links,
            template=template,
            strategy=strategy,
            strategy_decision_tree=strategy_decision_tree,
            hyperlinks_text=hyperlinks_text,
            precedent_summary=precedent_summary,
            precedent_link=precedent_link,
            precedent_meta=precedent_meta,
        )

        return prompt

    async def generate_mcq_question(
        self,
        user_query,
        llm1_answer,
        yes_count=0,
        template_data=None,
        max_score=0,
        report: Optional[str] = None,
    ):
        prompt = await self.build_mcq_prompt_full(
            user_query,
            llm1_answer,
            template_data or {},
            yes_count,
            max_score,
            report,
        )
        response = await self.llm.ainvoke(prompt)
        return response.content.strip()

    async def ask_human(
        self,
        user_query,
        llm1_answer=None,
        current_yes_count=0,
        template_data=None,
        initial_response: Optional[str] = None,
    ):
        # print("🔍 [ask_human] ES prefetch 시작")
        es_task = asyncio.create_task(async_ES_search_one([user_query]))

        # print("📦 [ask_human] 템플릿 로딩 중...")
        cached_data = retrieve_template_from_memory()
        accuracy = 0
        evaluating_now = False

        if cached_data and cached_data.get("built_by_llm2"):
            if not cached_data.get("updated_by_es"):
                # print("🧠 [ask_human] ES 기반 평가 수행 중...")
                evaluating_now = True
                await evalandsave_llm2_template_with_es(cached_data, user_query)
                cached_data["updated_by_es"] = True

            template_score = max(
                cached_data.get("template", {}).get("summary_score", 0),
                cached_data.get("template", {}).get("explanation_score", 0),
                cached_data.get("template", {}).get("ref_question_score", 0),
            )
            accuracy = calculate_llm2_accuracy_score(template_score, 0)
            cached_data["llm2_accuracy_score"] = accuracy
            store_template_in_memory(cached_data)
        elif cached_data:
            accuracy = cached_data.get("llm2_accuracy_score", 0)
        else:
            accuracy = 0

        # print("⏳ [ask_human] ES 결과 수집 대기")
        es_result = await es_task
        # print(f"✅ [ask_human] ES 완료, max_score={es_result.get('max_score')}")

        max_score = es_result.get("max_score", 0)
        hits = es_result.get("hits", [])

        # ✅ 2. 템플릿 불러오기
        cached_data = retrieve_template_from_memory()
        accuracy = 0
        evaluating_now = False

        # ✅ 3. 평가 수행 조건: LLM2 템플릿이 완성된 상태
        if cached_data and cached_data.get("built_by_llm2"):
            if not cached_data.get("updated_by_es"):
                evaluating_now = True
                await evalandsave_llm2_template_with_es(cached_data, user_query)
                cached_data["updated_by_es"] = True

            # ✅ 평가 점수는 항상 다시 계산
            template_score = max(
                cached_data.get("template", {}).get("summary_score", 0),
                cached_data.get("template", {}).get("explanation_score", 0),
                cached_data.get("template", {}).get("ref_question_score", 0),
            )
            accuracy = calculate_llm2_accuracy_score(template_score, max_score)
            cached_data["llm2_accuracy_score"] = accuracy
            store_template_in_memory(cached_data)

        # ✅ 템플릿이 없거나 아직 LLM2가 빌드되지 않은 경우
        elif cached_data:
            accuracy = cached_data.get("llm2_accuracy_score", 0)
        else:
            accuracy = 0


        # ✅ 4. fallback 판단 기준
        fallback_threshold = 15
        if 0 < accuracy < 50:
            fallback_threshold = int(15 + (50 - accuracy) * 0.5)

        if not evaluating_now and (
            (llm1_answer and "###no" in llm1_answer.lower())
            or (accuracy < 50 and max_score < fallback_threshold)
        ):

            return {
                "yes_count": 0,
                "mcq_question": (
                    "💡 이 질문은 법률적으로 명확하지 않을 수 있습니다.\n"
                    "가능하다면 조금 더 구체적으로 설명해 주시겠어요?"
                ),
                "is_mcq": False,
                "load_template_signal": False,
                "template": {},
            }

        # print("✅ [ask_human] LLM2 템플릿 사용 중")
        template_data = cached_data or template_data

        # ✅ 5. default 템플릿 (fallback에서 생성되는 경우)
        if not template_data:
            # print("⚠️ [ask_human] default 템플릿 생성 시작")
            titles = [item.get("title", "") for item in hits if item.get("title")]
            template_data = {
                "template": {
                    "summary": "당신은 친절한 상담사입니다.",
                    "explanation": "",
                    "ref_question": "",
                    "hyperlinks": [],
                },
                "strategy": {
                    "final_strategy_summary": "",
                    "tone": "친절하고 명확한 말투",
                    "structure": "문제제기 → 법적요건 → 결론",
                    "decision_tree": [
                        f"사용자가 '{title}' 관련 질문을 하면 법적 요건으로 판단"
                        for title in titles[:3]
                    ],
                },
                "precedent": {},
            }

        # ✅ 6. YES 감지 및 누적
        yes_count_detected = 1 if llm1_answer and "###yes" in llm1_answer.lower() else 0
        total_yes_count = current_yes_count + yes_count_detected

        # ✅ 7. 후속 질문 생성
        mcq_q = await self.generate_mcq_question(
            user_query, llm1_answer or "", total_yes_count, template_data
        )
        if total_yes_count >= 2:
            mcq_q = f"{mcq_q}\n\n[저장된 템플릿 사용됨]"

        # ✅ 8. 병합 응답
        combined = (
            f"{initial_response.strip()}\n\n🧩 [후속 질문 제안]\n{mcq_q.strip()}"
            if initial_response
            else mcq_q.strip()
        )

        return {
            "yes_count": total_yes_count,
            "mcq_question": combined,
            "is_mcq": True,
            "load_template_signal": total_yes_count >= 2,
            "template": template_data,
        }
