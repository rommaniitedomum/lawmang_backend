import os
import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from app.chatbot.tool_agents.tools import async_search_consultation
from app.chatbot.tool_agents.utils.utils import validate_model_type
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def build_relevance_prompt(user_query: str, consultation_results: List[Dict]) -> str:
    formatted = "\n\n".join(
        [
            f"{idx + 1}. 제목: {item['title']}\n질문: {item['question']}"
            for idx, item in enumerate(consultation_results)
        ]
    )
    return f"""
당신은 법률 상담 전문가입니다.

사용자의 질문은 다음과 같습니다:
\"{user_query}\"

아래는 사용자 질문과 관련이 있을 수 있는 기존 상담들입니다.

각 항목은 '제목', '질문'으로 구성되어 있습니다.  
→ 만약 아래 상담들이 사용자 질문과 **주제적으로 완전히 무관**하다면, "irrelevant"라고만 응답하세요.  
→ 일부라도 관련이 있다면, "relevant"라고만 응답하세요.

===== 상담 목록 =====
{formatted}
""".strip()


async def check_relevance_to_consultations(
    user_query: str,
    consultation_results: List[Dict],
    model: str = "gpt-3.5-turbo",
) -> bool:
    validate_model_type(model)
    if not consultation_results:
        return False

    prompt = build_relevance_prompt(user_query, consultation_results)

    llm = ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        streaming=False,
    )

    messages = [
        {
            "role": "system",
            "content": "당신은 법률 상담 질문의 주제 관련성을 판별하는 AI입니다.",
        },
        {"role": "user", "content": prompt},
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content.strip().lower()
    return result_text == "relevant"


def build_choose_one_prompt(user_query: str, consultation_results: List[Dict]) -> str:
    formatted = "\n\n".join(
        [
            f"{idx + 1}. 제목: {item['title']}\n질문: {item['question']}\n답변: {item['answer']}"
            for idx, item in enumerate(consultation_results)
        ]
    )
    return f"""
당신은 법률 상담 전문가입니다.

사용자의 질문은 다음과 같습니다:
"\{user_query}\"

아래는 사용자 질문과 **법률적으로 관련이 있을 수 있는 상담 데이터 목록**입니다.  
각 항목은 제목, 질문, 답변으로 구성되어 있으며, 일부는 유사해 보이지만 실제 쟁점이 다를 수 있습니다.

💡 유의사항:
- 상담 목록에는 실제 사용자 질문과 **주제가 다른 사례**도 포함되어 있을 수 있습니다.
- 특히 **법률적 핵심 쟁점**(예: 고의/과실, 명예훼손, 불법행위, 인과관계 등)이 **일치하지 않는 경우**에는 관련 사례로 선택하지 마세요.
- 단순히 표현이 비슷하거나 언뜻 유사해 보여도, 질문의 핵심 쟁점이 다르면 선택하면 안 됩니다.

✅ 반드시 사용자 질문에 **가장 정확하게 대응할 수 있는 상담 한 건만 선택**하세요.  
✅ 선택 기준은 "**질문의 핵심 법률 쟁점과 가장 일치하는 상담**"입니다.  
⛔ 판단 기준은 **질문 중심**입니다. **답변만 보고 선택하지 마세요.**

→ 아래 형식의 **JSON 배열로만 응답**하세요.  
선택할 항목 번호만 포함한 리스트를 출력해야 하며, 텍스트 설명은 금지입니다.

예시:  
[2]

→ 사용자 질문과 관련된 항목이 **전혀 없다면**, 빈 배열을 반환하세요.

예시:  
[]

===== 상담 목록 =====
{formatted}
""".strip()


async def choose_best_consultation(
    user_query: str,
    consultation_results: List[Dict],
    model: str = "gpt-3.5-turbo",
) -> Dict:
    if not consultation_results:
        return {"error": "🔍 관련된 상담 결과가 없습니다.", "status": "no_result"}

    prompt = build_choose_one_prompt(user_query, consultation_results)

    llm = ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
        streaming=False,
    )

    messages = [
        {
            "role": "system",
            "content": "당신은 법률 상담 데이터를 정제하는 AI 전문가입니다.",
        },
        {"role": "user", "content": prompt},
    ]

    response = await llm.ainvoke(messages)
    result_text = response.content

    if result_text.strip() in ["[]", "[0]"]:
        return {"error": "🙁 관련된 상담이 없습니다.", "status": "irrelevant"}

    try:
        selected = json.loads(result_text)
        selected_index = int(selected[0]) if isinstance(selected, list) else None

        if selected_index and 0 < selected_index <= len(consultation_results):
            return consultation_results[selected_index - 1]
        else:
            return {
                "error": "❗ 선택된 인덱스가 유효하지 않습니다.",
                "status": "invalid_index",
            }

    except Exception:
        # print("❌ 응답 파싱 실패:", e)
        return {"error": "❗ GPT 응답을 이해할 수 없습니다.", "status": "parse_error"}


# ✅ 전체 흐름# ✅ 전체 흐름 - 수정본
async def run_consultation_qualifier(
    user_query: str,
    consultation_results: List[Dict],  # 외부에서 검색된 결과를 받음
    model: str = "gpt-3.5-turbo",
) -> Dict:
    """
    📌 FAISS 기반 유사 상담 검색 → LLM 기반 관련성 판단 → 최적 상담 선택 흐름
    """

    # ❌ 중복 검색 제거
    # consultation_results, _, _ = await async_search_consultation([user_query])

    if not consultation_results:
        return {"error": "🔍 관련된 상담 결과가 없습니다.", "status": "no_result"}

    is_relevant = await check_relevance_to_consultations(
        user_query, consultation_results, model=model
    )
    if not is_relevant:
        return {
            "error": "🙁 사용자 질문과 관련된 상담이 없습니다. 질문을 다시 작성해보세요.",
            "status": "no_match",
        }

    return await choose_best_consultation(user_query, consultation_results, model=model)

    # fallback 보완: title/answer/question 키가 없으면 fallback 값 포함하여 반환
    # if not isinstance(result, dict) or not all(
    #     k in result for k in ["title", "question", "answer"]
    # ):
    #     print("⚠️ [Qualifier Fallback Triggered] 유효한 상담 데이터를 찾지 못함.")
    #     return {
    #         "title": "법률 일반",
    #         "question": user_query,
    #         "answer": "해당 질문에 대한 정확한 상담 데이터를 찾지 못했으나, 일반적인 법률 지식에 기반해 응답을 생성합니다.",
    #         "status": "fallback_triggered",
    #     }

    # return result
