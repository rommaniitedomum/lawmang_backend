import json
from typing import Optional


def get_prompt_by_score(
    max_score: Optional[float],
    user_query: str = "",
    summary_with_links: str = "",
    explanation_with_links: str = "",
    template: dict = {},
    strategy: dict = {},
    strategy_decision_tree: str = "",
    precedent_summary: str = "",
    precedent_link: str = "",
    precedent_meta: str = "",
    hyperlinks_text: str = "",
) -> str:
    if max_score is None:
        max_score = 0  # 또는 default fallback 값 (예: 20)

    if max_score > 80:
        return f"""
당신은 전략과 판례 요약이 모두 포함된 고신뢰도 템플릿을 바탕으로,  
최종 사용자 응답을 구성하는 GPT입니다.

Let's plan our reasoning step by step, then generate a final response.  
After writing, make sure to review whether your answer is user-appropriate and legally sound.

---

📌 [사용자 질문]  
{user_query}

📄 [요약]  
{summary_with_links}

📄 [설명]  
{explanation_with_links}

📋 [참고 질문]  
{template.get("ref_question", "해당 없음")}

🔗 [하이퍼링크]  
{hyperlinks_text}

🧩 [전략 요약]  
{strategy.get("final_strategy_summary", "")}

📋 [응답 구성 전략] (Few-shot 기반 예시 포함)  
- 말투: {strategy.get("tone", "")}  
- 흐름: {strategy.get("structure", "")}  
- 조건 흐름도:
{strategy_decision_tree}

🔗 [추천 링크]  
{json.dumps(strategy.get("recommended_links", []), ensure_ascii=False)}

📚 [판례 요약] (판단하여 신뢰도 낮으면 생략)  
- {precedent_summary}  
- 링크: {precedent_link}  
- 정보: {precedent_meta}

---

🛠 단계별 응답 계획 (ReAct-style Planning):

1. 질문자의 감정·상황을 고려해 말투(tone)를 결정하세요.  
→ Why? 실제 도움이 되는 답변은 사용자의 맥락을 먼저 반영해야 신뢰를 얻습니다.

2. 응답 구조를 설계하세요: 공감 → 요약 → 법률 설명 → 대응 전략  
→ Why? 구조는 설득력과 전달력의 핵심입니다.

3. 조건 흐름(판단 분기)을 Tree-of-Thought 형식으로 표현하세요.  
→ ex: "A 조건이 충족되는가? → 예: ..., 아니오: ..."  
→ Why? 사용자 상황에 따라 다른 결론을 제시할 수 있어야 합니다.

4. 실제 내용을 작성하세요.  
→ 모든 요약 및 전략 정보는 반드시 반영되어야 합니다.  
→ 구체적인 대응책, 실무 조언, 법적 판단, 최신 판례 해석 포함

---

✅ [출력 필수 요소]

🔲 ✅ 결론 및 권고 사항  
- 법적 주의사항 안내  
- 실무적 대응 방안 제공  
- 사건 해결 방향 제안  
- 참고 링크 제공

🔲 ✅ 법률 판단 및 논리 전개  
- 관련 법령 설명  
- 판례 분석 및 적용 가능성 설명  
- 유사 사례 비교  
- 법적 쟁점 도출 가능성 평가

🔲 ✅ 최근 판례/개정 동향 분석  
- 해당 법령 조항 적용 가능성  
- 주요 판례 정리 및 사실관계 비교

---

💬 Self-Evaluation 단계 (출력 마지막에만 LLM 내부적으로 판단):

이 응답은 사용자 맞춤성과 법적 명확성을 모두 충족하는가?

1. 이 전략은 질문자의 상황(정황, 표현, 맥락)에 실질적으로 도움이 되는가?  
2. 문장 흐름이 자연스럽더라도, **조건 누락**이나 **사건 유형 오적용**은 없는가?

→ 위 기준에 부합하지 않으면 응답을 수정하여 다시 작성하세요.  
→ 사용자에게 혼란을 주는 일반론, 표현 모호성, 과장된 조언은 금지입니다.
"""


    elif max_score > 40:
        return f"""
📌 사용자의 질문에 대해 명확히 요구사항을 파악하고,
전략 요약을 바탕으로 구조화된 응답을 작성해 주세요.

[사용자 질문]
{user_query}

[전략 요약]
{strategy.get("final_strategy_summary", "")}

[예상 흐름]
- 말투: {strategy.get("tone", "")}
- 구조: {strategy.get("structure", "")}

필요시 판례 요약을 참조하세요:
- {precedent_summary}

※ 설명과 판단을 간결하게 연결하여 작성해 주세요.

📌 다음 구성 요소들을 반드시 포함해야 합니다:

🔲 ✅ 결론 및 권고 사항
- 법적 주의사항 안내
- 실무적 대응 방안 제공
- 사건 해결 방향 제안

🔲 ✅ 법률 판단 및 논리 전개
- 관련 법령 설명
- 판례 분석 및 적용 가능성 설명
- 유사 사례 비교
- 법적 쟁점 도출 가능성 평가
"""

    elif max_score > 20:
        return f"""
😊 이 프롬프트는 친절한 변호사의 말투로 구성되어야 합니다.
ES 기반 정보를 부드럽게 인용하며, 사용자가 이해하기 쉬운 어조로 안내해 주세요.
🔲 ✅ 결론 및 권고 사항
- 법적 주의사항 안내
- 실무적 대응 방안 제공
- 사건 해결 방향 제안
[사용자 질문]: {user_query}
"""
    else:
        return f"""
🤔 검색 결과가 낮거나 존재하지 않습니다.
기본적인 법률 지식과 사용자 질문만을 바탕으로 보편적인 안내를 생성해 주세요.
🔲 ✅ 결론 및 권고 사항
- 법적 주의사항 안내
- 실무적 대응 방안 제공
- 사건 해결 방향 제안
[질문]: {user_query}
"""
