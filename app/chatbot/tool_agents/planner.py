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

Let's think step by step and explain why each part is valid.

---

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
    → Why? 질문자의 경험과 서술은 응답에서 반드시 존중받아야 하며, 법적 조언은 현실과 맞닿아야 하기 때문입니다.

✅ 참고 상담 중 사용자 질문과 **법률적으로 관련 있는 모든 레퍼런스(문장, 개념, 조항 등)**는 전략 구성에 반드시 반영하세요.  
⛔ 단, 사용자 질문의 핵심 쟁점과 어긋나는 내용은 인용하거나 참고하지 마세요.  
→ Why? 핵심 쟁점과 무관한 정보는 오히려 잘못된 방향으로 안내할 수 있기 때문입니다.

---

다음 네 가지 항목을 순서에 맞춰 작성하세요:  
각 항목은 단순 생성이 아니라, 그 **선택과 전개가 합리적인 근거에 기반**하도록 설계되어야 합니다.  
각 문단 내부에서는 “왜 이렇게 판단했는가”를 LLM이 스스로 납득하며 작성하세요.

---

1. **summary**  
- 사용자 질문에서 드러난 핵심 법률 쟁점과 손해 또는 갈등의 원인을 한 문단으로 요약합니다.  
- 질문에 포함된 표현과 정황을 명시적으로 포함하며, 단순히 ‘가능/불가능’으로 결론 짓지 마세요.  
→ Why? 질문자는 결론보다 **상황을 명확히 해석받고 싶어 하며**, 정황 중심의 요약이 신뢰를 형성합니다.

2. **explanation**  
- 사용자의 상황과 감정을 먼저 언급하며 공감을 표현하세요 (예: 억울함, 당황스러움 등).  
- 이어서 법률적으로 중요한 쟁점을 짚고, 실무상 현실적인 해석과 전략적 선택지를 설명하세요.  
- "실제 법원에서는", "현실적으로는", "실무상으로는" 등의 표현을 활용해 실질적 조언을 제공하세요.  
- 유사 상담 내용이 도움이 되는 경우, 해당 내용은 전략적으로 요약하여 인용할 수 있습니다.  
→ Why? 사용자는 법리 해석보다 **실제 도움이 되는 말**을 원하며, 감정적 연결이 설득의 기반이 됩니다.

3. **hyperlinks**  
- 설명에서 언급한 법령, 판례 등을 실제 출처와 함께 label + URL 형식으로 정리하세요.  
- law.go.kr 공식 사이트 링크를 사용하세요.  
→ Why? 제시된 정보의 신뢰성을 높이고, 사용자가 직접 검토할 수 있도록 하려는 목적입니다.

4. **ref_question**  
- 반드시 사용자 질문(user_query)을 **그대로** 반환하세요.  
- SQL 상담 질문이 아닌 **사용자 질문이 기준**입니다.  
→ Why? 생성 응답은 항상 원 질문 기준으로 소급 가능해야 하며, 회고적 검토의 기준점이 되어야 하기 때문입니다.

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
Let's think step by step and explain why each part is valid.

[사용자 질문]
"{user_query}"

[설명 초안]
"{explanation}"

[관련 법률 링크]
{hyperlink_text}

[이전 전략이 있는 경우 참고용]
{previous_strategy_text}

--- 작업 지시 ---

💡 아래 응답 내용 중 일부는 오답이 포함되어 있을 수 있습니다.  
→ Why? 생성형 AI의 응답은 종종 정확도나 문맥상 오류가 존재할 수 있으므로, 반드시 사용자 입장에서 확인하고 판단해야 합니다.

💡 제공된 설명이 사용자 질문과 주제가 명백히 다른 경우, 해당 문장은 반드시 삭제해야 합니다.  
→ Why? 핵심 쟁점과 무관한 정보는 잘못된 전략을 유도하거나 신뢰도를 떨어뜨릴 수 있습니다.  

예: 가족이 상해를 당했습니다 → 이혼 관련 판례는 제외  

다음 항목들을 순서에 맞춰 작성하세요.  
각 항목은 단순 요약이 아니라, "왜 이렇게 판단했는가?"에 대해 LLM이 내부적으로 설명 가능해야 합니다.

1. **tone**  
- 사용자의 감정, 상황, 질문 맥락을 고려해 응답의 말투를 설계하세요.  
→ Why? 말투는 단순 표현을 넘어, 사용자의 수용성과 신뢰도에 직접적인 영향을 줍니다.

2. **structure**  
- 응답을 어떤 흐름으로 구성할지 단계별로 설명하세요. (예: 공감 → 쟁점 요약 → 조언 → 법령 요약 등)  
→ Why? 일관된 흐름은 사용자 이해를 돕고, 과도한 정보 혼란을 방지합니다.

3. **decision_tree**  
- 법률 판단에 필요한 조건/예외 분기를 **Tree-of-Thought** 형식으로 구성하세요.  
→ Why? 후속 LLM이 이 구조를 기반으로 논리적으로 판단하거나 요약할 수 있도록 해야 합니다.  

4. **final_strategy_summary**  
- 전체 전략을 한 문단으로 요약하세요.  
→ Why? 요약은 사용자뿐 아니라, 시스템 간 공유에도 유리한 정보 축약 지점입니다.

5. **recommended_links**  
- 설명에서 언급한 법령이나 판례 링크를 `label + URL (law.go.kr)` 형식으로 정리하세요.  
→ Why? 사용자에게 신뢰할 수 있는 출처를 제공함으로써 정보의 공식성을 확보할 수 있습니다.


--- 🧠 결정 트리 예시 (Few-shot / Tree-of-Thought 구조) ---

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
1. GPT 전략이 Tavily 요약 결과의 **핵심 쟁점 및 법률 논리를 충실히 반영**하고 있는지 평가하세요.  
→ Why? 핵심 요소가 누락되었거나 법리와 다르면 사용자에게 잘못된 안내가 될 수 있습니다.

2. 표현 방식이나 문장 순서가 달라도, **핵심 내용이 일치한다면** 긍정 평가하세요.  
→ Why? 동일한 의미를 담고 있다면 표현의 차이는 문제가 되지 않습니다.

3. 전략이 오해를 유발하거나, 사실관계/책임관계의 흐름에 **명백한 오류**가 있다면 부정 평가하세요.

---

🧪 최종 판단:

- 전략이 **충분히 유효하고, 실무적으로도 문제없다면**: `true`
- 전략이 **중대한 누락, 오류, 비현실적 조언**을 포함한다면: `false`

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
Let's think step by step and explain why each part is valid.

당신은 다른 LLM이 참조할 수 있는 **완성된 법률 전략 프롬프트를 생성하는 생성형 에이전트**입니다.  
입력으로 주어진 전략은 일부 불완전하거나 모호할 수 있으며, 이를 명확하게 보강해야 합니다.

아래 Tavily 요약을 참고하여 전략을 보완하세요.
[Tavily 요약들]
{combined_snippets}

[기존 전략 요약]
{original_strategy.get("final_strategy_summary", "")}

--- 작업 지시 ---
1. 기존 전략 내용을 가능한 한 활용하되, **Tavily 요약의 핵심 법리/논점 정보를 반드시 반영**하세요.  
→ Why? 기존 전략의 문체와 흐름을 살리되, 부족한 정보를 보완하여 신뢰도를 높이기 위함입니다.

2. **Tavily**라는 단어는 절대 사용하지 마세요.  
⛔ “Tavily에 따르면”, “출처: Tavily”, “Tavily 요약” 등 **모든 형태의 직접 인용은 금지**  
→ Why? 사용자에게 외부 출처가 노출되면 혼란이나 신뢰 저하가 발생할 수 있습니다.

3. **응답 구조(JSON 필드)는 그대로 유지**해야 하며,  
   `tone`, `structure`, `decision_tree`, `final_strategy_summary`, `recommended_links` 순서로 작성하세요.


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
