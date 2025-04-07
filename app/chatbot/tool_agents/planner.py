import os
import json
import difflib
from app.chatbot.tool_agents.tools import async_ES_search
from langchain_openai import ChatOpenAI
from typing import List, Dict
from app.chatbot.tool_agents.tools import LawGoKRTavilySearch
from app.chatbot.memory.templates import get_default_strategy_template
from app.chatbot.tool_agents.utils.utils import validate_model_type
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def get_llm(model: str, temperature: float = 0.3) -> ChatOpenAI:
    validate_model_type(model)  # ✅ 타입 체크

    return ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        temperature=temperature,
        streaming=False,
    )


# ✅ 응답 템플릿 생성
async def generate_response_template(
    title: str,
    question: str,
    answer: str,
    user_query: str,
    es_results: list[dict] = None,
    model: str = "gpt-3.5-turbo",
) -> dict:
    # ✅ es_results가 없으면 직접 호출
    if es_results is None:
        es_results = await async_ES_search([user_query])

    # 🔹 ES 상담 내용 추가 구성
    es_context = ""
    if es_results:
        es_context += "ES에서 검색한 유사 상담 3건:\n"
        for i, item in enumerate(es_results, start=1):
            es_context += f"\n📌 [{i}번 상담]\n"
            es_context += f"- 제목(title): {item.get('title', '')}\n"
            es_context += f"- 질문(question): {item.get('question', '')}\n"
            es_context += f"- 답변(answer): {item.get('answer', '')}\n"

    prompt = f"""
당신은 법률 상담 응답 템플릿을 구성하는 AI입니다.

사용자의 질문:
"{user_query}"

{es_context}

선택된 대표 상담(title):
"{title}"

상담 질문(question):
"{question}"

상담 답변(answer):
"{answer}"

--- 작업 지시 ---
💡 제공된 답중에는 오답이 섞여 있습니다 천천히 생각해보고 사용자 입장에서 올바른 답변을 해보세요.
1. 사용자가 이해하기 쉽게 핵심 내용을 요약하세요 (summary).
2. 요약을 바탕으로, 상담 답변의 내용을 일반인이 이해할 수 있도록 풀어서 설명하세요 (explanation).
3. 답변과 관련된 법령/판례가 있다면 하이퍼링크 형태로 제공하세요. label과 url을 포함한 리스트 형식 (hyperlinks).
4. 그리고 이 상담에서 사용된 `question`은 참고용 질문이므로 'ref_question'이라는 key로 반환하세요.

--- 응답 예시 ---
{{
  "summary": "...",
  "explanation": "...",
  "hyperlinks": [{{"label": "...", "url": "..."}}],
  "ref_question": "..."
}}
"""

    llm = get_llm(model, temperature=0.3)

    messages = [
        {
            "role": "system",
            "content": "당신은 법률 응답 템플릿을 생성하는 전문가입니다.",
        },
        {"role": "user", "content": prompt},
    ]

    try:
        response = llm.invoke(messages)
        return json.loads(response.content)
    except Exception:
        return {"error": "GPT 응답 파싱 실패"}


# ✅ 전략 생성
async def generate_response_strategy(
    explanation: str,
    user_query: str,
    hyperlinks: list = None,
    previous_strategy: dict = None,
    model: str = "gpt-3.5-turbo",
) -> dict:
    hyperlinks = hyperlinks or []

    hyperlink_text = (
        "\n".join([f"- {item['label']}: {item['url']}" for item in hyperlinks])
        if hyperlinks
        else "없음"
    )

    previous_strategy_text = (
        json.dumps(previous_strategy, ensure_ascii=False, indent=2)
        if previous_strategy
        else "없음"
    )

    prompt = f"""
당신은 법률 응답 전략을 설계하는 전문가입니다.

[사용자 질문]
"{user_query}"

[설명 초안]
"{explanation}"

[관련 법률 링크]
{hyperlink_text}

[이전 전략이 있는 경우 참고용]
{previous_strategy_text}

--- 작업 지시 ---
💡 제공된 답중에는 오답이 섞여 있습니다 천천히 생각해보고 사용자 입장에서 올바른 답변을 해보세요.
💡 제공된 답변에 사용자 질문과 주제가 명백히 다른것이 존재하면 삭제해버리세요
ex: 가족이 상해를 당했습니다 -> 이혼관련 판례 

1. 이전 전략이 있다면 최대한 활용하여 보완된 전략을 설계하세요.
2. 사용자 경험을 고려해 적절한 말투(tone/style)를 설계하세요.  
3. 응답 흐름 구조를 설명하세요.  
4. 조건/예외 흐름이 있다면 decision_tree 형식으로 만드세요.  
5. 전체 전략을 요약하세요.  
6. 추천 링크를 리스트로 정리하세요.

응답 형식 (JSON):
{{
  "tone": "...",
  "structure": "...",
  "decision_tree": ["..."],
  "final_strategy_summary": "...",
  "recommended_links": [{{"label": "...", "url": "..."}}]
}}
"""

    llm = get_llm(model, temperature=0.3)

    messages = [
        {"role": "system", "content": "당신은 법률 상담 전략을 설계하는 AI입니다."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = llm.invoke(messages)
        strategy_raw = response.content
        strategy = json.loads(strategy_raw)
    except Exception as e:
        default_strategy = get_default_strategy_template()
        default_strategy["error"] = "GPT 전략 파싱 실패"
        return default_strategy

    search_tool = LawGoKRTavilySearch(max_results=3)
    tavily_results = search_tool.run(user_query)

    evaluation = await evaluate_strategy_with_tavily(strategy, tavily_results)
    strategy["evaluation"] = evaluation

    return strategy


# ✅ 전략 평가
async def evaluate_strategy_with_tavily(
    strategy: dict,
    tavily_results: list,
    model: str = "gpt-3.5-turbo",
) -> dict:
    if not tavily_results or not isinstance(tavily_results, list):
        return {
            "needs_revision": False,
            "reason": "Tavily 결과가 없거나 유효하지 않음",
            "tavily_snippets": [],
        }

    tavily_snippets = [
        (result.get("content") or result.get("snippet") or result.get("text")).strip()
        for result in tavily_results[:3]
        if result.get("content") or result.get("snippet") or result.get("text")
    ]

    if not tavily_snippets:
        return {
            "needs_revision": False,
            "reason": "Tavily 요약 추출 실패",
            "tavily_snippets": [],
        }

    combined = "\n\n".join(
        [f"[요약 {i + 1}]\n{text}" for i, text in enumerate(tavily_snippets)]
    )

    prompt = f"""
당신은 법률 상담 전략을 평가하는 AI입니다.

[GPT 전략 요약]
{strategy.get("final_strategy_summary", "")}

[Tavily 요약 결과들]
{combined}

--- 작업 지시 ---
GPT 전략이 부실하거나 중요한 정보를 누락했는지 평가하세요.
아래 JSON으로만 응답하세요.

{{
  "needs_revision": true or false,
  "reason": "...",
  "tavily_snippets": [...]
}}
"""

    llm = get_llm(model, temperature=0.2)
    messages = [
        {"role": "system", "content": "법률 분석가 AI입니다."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = llm.invoke(messages)
        return json.loads(response.content)
    except Exception as e:
        return {
            "needs_revision": False,
            "reason": "GPT 응답 파싱 실패",
            "tavily_snippets": tavily_snippets,
        }


# ✅ 전략 보완
async def revise_strategy_with_feedback(
    original_strategy: dict,
    tavily_snippets: list,
    model: str = "gpt-3.5-turbo",
) -> dict:
    combined_snippets = "\n\n".join(
        [
            f"[Tavily 요약 {i + 1}]\n{snippet}"
            for i, snippet in enumerate(tavily_snippets)
        ]
    )

    prompt = f"""
GPT가 만든 기존 전략이 너무 모호하거나 핵심 정보를 누락한 것으로 판단됩니다.  
아래 Tavily 요약을 참고하여 전략을 보완하세요.
[Tavily 요약들]
{combined_snippets}

[기존 전략 요약]
{original_strategy.get("final_strategy_summary", "")}

--- 작업 지시 ---
- 기존 전략을 기반으로 하되, Tavily의 법령 요약을 반영하여 더 명확하게 수정하세요.
- 전체 전략 JSON 구조는 유지하세요.

응답 형식 (JSON):{{
  "tone": "...",
  "structure": "...",
  "decision_tree": ["..."],
  "final_strategy_summary": "...",
  "recommended_links": [{{"label": "...", "url": "..."}}]
}}
"""

    llm = get_llm(model, temperature=0.2)
    messages = [
        {"role": "system", "content": "당신은 전략 보완 전문가입니다."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = llm.invoke(messages)
        return json.loads(response.content)
    except Exception as e:
        return get_default_strategy_template()


# ✅ 전략 실행 흐름
async def run_response_strategy_with_limit(
    explanation,
    user_query,
    hyperlinks,
    model="gpt-3.5-turbo",
    previous_strategy: dict = None,  # ✅ 추가
):
    strategy = await generate_response_strategy(
        explanation=explanation,
        user_query=user_query,
        hyperlinks=hyperlinks,
        previous_strategy=previous_strategy,  # ✅ 전달
        model=model,
    )

    if strategy.get("evaluation", {}).get("needs_revision") is True:
        revised = await revise_strategy_with_feedback(
            original_strategy=strategy,
            tavily_snippets=strategy["evaluation"].get("tavily_snippets", []),
        )
        revised["evaluation"] = {"revised": True}
        return revised

    return strategy
