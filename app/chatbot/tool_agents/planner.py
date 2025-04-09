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

📌 사용자 질문:
"{user_query}"

📎 참고자료 (ES 검색 기반 상담):
{es_context}

📎 SQL 기반 유사 상담:
- 제목(title): "{title}"
- 질문(question): "{question}"
- 답변(answer): "{answer}"

---

🛠 작업 지시:

💡 아래 상담 예시에는 오답이 섞여 있을 수 있으므로 주의 깊게 검토하세요.  
💡 상담 예시는 참고용일 뿐이며, 반드시 **사용자 질문을 중심으로 판단**하고 응답 전략을 구성해야 합니다.  
💡 사용자 질문은 **최소한의 요구사항이자 응답의 중심**입니다.  
    - 질문에 포함된 **사실관계, 표현, 정황**을 빠짐없이 반영하세요.  
    - 그 위에 법률적 해석을 덧붙여 **전략적으로 구성**해야 합니다.

✅ 참고 상담 중 사용자 질문과 **법률적으로 관련 있는 모든 레퍼런스(문장, 개념, 조항 등)**는 전략 구성에 반드시 반영하세요.  
⛔ 단, 사용자 질문의 핵심 쟁점과 어긋나는 내용은 인용하거나 참고하지 마세요.  

---

다음 네 가지 항목을 순서에 맞춰 작성하세요:

1. **summary**  
- 사용자 질문에서 드러난 핵심 법률 쟁점과 손해 또는 갈등의 원인을 한 문단으로 요약합니다.  
- 질문에 포함된 표현과 정황을 명시적으로 포함하며, 단순히 ‘가능/불가능’으로 결론 짓지 마세요.

2. **explanation**  
- 사용자의 상황과 감정을 먼저 언급하며 공감을 표현하세요 (예: 억울함, 당황스러움 등).  
- 이어서 법률적으로 중요한 쟁점을 짚고, 실무상 현실적인 해석과 전략적 선택지를 설명하세요.  
- "실제 법원에서는", "현실적으로는", "실무상으로는" 등의 표현을 활용해 실질적 조언을 제공하세요.  
- 유사 상담 내용이 도움이 되는 경우, 해당 내용은 전략적으로 요약하여 인용할 수 있습니다.

3. **hyperlinks**  
- 설명에서 언급한 법령, 판례 등을 실제 출처와 함께 label + URL 형식으로 정리하세요.  
- law.go.kr 공식 사이트 링크를 사용하세요.

4. **ref_question**  
- 반드시 사용자 질문(user_query)을 **그대로** 반환하세요.  
- SQL 상담 질문이 아닌 **사용자 질문이 기준**입니다.

---

🧾 응답 형식 예시:

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
💡 제공된 답변에 사용자 질문과 주제가 명백히 다른 내용이 존재하면 삭제하세요.  
예: 가족이 상해를 당했습니다 → 이혼 관련 판례는 제외  

1. 이전 전략이 있다면 최대한 활용하여 보완된 전략을 설계하세요.  
2. 사용자 경험을 고려해 적절한 말투(tone/style)를 설계하세요.  
3. 응답 흐름 구조를 설명하세요.  
4. 조건/예외 흐름이 있다면 decision_tree 형식으로 만드세요.  
5. 전체 전략을 요약하세요.  
6. 추천 링크를 리스트로 정리하세요.

--- 결정 트리 예시 (Few-shot) ---

예:  
"사용자가 작업 중 고소를 당해 일을 놓쳤다고 질문한 경우"

decision_tree: [
  "1. 고소가 사실에 근거한 정당한 고소인가?",
  "   ├─ 예: 손해배상 청구 어려움 → 고소는 정당한 권리 행사이므로 불법행위 성립 안 됨",
  "   └─ 아니오: 허위 또는 악의적 고소 → 불법행위 성립 가능성 → 손해배상 청구 가능",
  "2. 고소와 손해 사이 인과관계가 명확한가?",
  "   ├─ 예: 실제 손해(일실수익 등)를 입증할 수 있다면 배상 인정 가능",
  "   └─ 아니오: 고소와 손해가 무관하거나 추정 수준 → 손해배상 인정 어려움"
]

--- end ---

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
⛔ 예: “Tavily에 따르면”, “Tavily 요약에 의하면”, “출처: Tavily” 등은 절대 금지  
⛔ 단어 "Tavily"는 응답 JSON 어디에도 등장해서는 안 됩니다. 전략 판단에만 참고하세요.
- 전체 전략 JSON 구조는 유지하세요.

--- 결정 트리 예시 (Few-shot) ---

예:  
"사용자가 작업 중 고소를 당해 일을 놓쳤다고 질문한 경우"

decision_tree: [
  "1. 고소가 사실에 근거한 정당한 고소인가?",
  "   ├─ 예: 손해배상 청구 어려움 → 고소는 정당한 권리 행사이므로 불법행위 성립 안 됨",
  "   └─ 아니오: 허위 또는 악의적 고소 → 불법행위 성립 가능성 → 손해배상 청구 가능",
  "2. 고소와 손해 사이 인과관계가 명확한가?",
  "   ├─ 예: 실제 손해(일실수익 등)를 입증할 수 있다면 배상 인정 가능",
  "   └─ 아니오: 고소와 손해가 무관하거나 추정 수준 → 손해배상 인정 어려움"
]

--- end ---

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
