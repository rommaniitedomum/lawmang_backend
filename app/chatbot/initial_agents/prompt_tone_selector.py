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
[사용자 질문]
{user_query}
[요약]
{summary_with_links}
[설명]
{explanation_with_links}
[전략 요약]
{strategy.get("final_strategy_summary", "")}
[응답 구성 전략]
- 말투: {strategy.get("tone", "")}
- 흐름: {strategy.get("structure", "")}
- 조건 흐름도:
{strategy_decision_tree}
[추가된 판례 요약]
- {precedent_summary}
- 정보: {precedent_meta}


[링크1]
{hyperlinks_text}
💡 제공된 답중에는 오답이 섞여 있습니다 천천히 생각해보고 사용자 입장에서 올바른 답변을 해보세요.
💡 위 내용을 반영하여, 사용자가 신뢰할 수 있는 법률 상담을 생성하세요.
LLM2가 구성한 판례/전략/설명을 충분히 반영하여, 구조적이고 논리적인 전문 법률 답변을 생성해 주세요.
📌 다음 구성 요소들을 반드시 포함해야 합니다:

----------------------------
[결론 및 권고]
- 사건의 법적 평가 요약
- 대응 방안 및 권고

🔲 ✅ 법률 판단 및 논리 전개
- 관련 법령 설명
- 판례 분석 및 적용 가능성 설명
- 유사 사례 비교
- 법적 쟁점 도출 가능성 평가

🔲 ✅ 최근 판례/개정 동향 분석
- 해당 법령 조항 적용 가능성
- 주요 판례 정리 및 사실관계 비교
-----------------------------

"""
    elif max_score > 60:
        return f"""
📘 이 프롬프트는 설명 중심의 템플릿입니다.

[사용자 질문]
{user_query}

[요약]
{summary_with_links}

[설명]
{explanation_with_links}

[전략 요약]
{strategy.get("final_strategy_summary", "")}

[판례 요약]
- {precedent_summary}
- 링크: {precedent_link}
💡 제공된 답중에는 오답이 섞여 있습니다 천천히 생각해보고 사용자 입장에서 올바른 답변을 해보세요.
💡 위 내용을 반영하여, 사용자가 이해하기 쉽도록 설명 위주로 응답을 작성해 주세요.
구조는 자유롭게 하되, 핵심 내용을 놓치지 마세요.

📌 다음 구성 요소들을 반드시 포함해야 합니다:

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

[결론 및 권고]
- 사건의 법적 평가 요약
- 대응 방안 및 권고

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
------------------------------
🔲 ✅ 결론 및 권고 사항
- 법적 주의사항 안내
- 실무적 대응 방안 제공
- 사건 해결 방향 제안
[사용자 질문]: {user_query}
------------------------------
"""
    else:
        return f"""
🤔 검색 결과가 낮거나 존재하지 않습니다.
기본적인 법률 지식과 사용자 질문만을 바탕으로 보편적인 안내를 생성해 주세요.
------------------------------
🔲 ✅ 결론 및 권고 사항
- 법적 주의사항 안내
- 실무적 대응 방안 제공
- 사건 해결 방향 제안
[질문]: {user_query}
------------------------------
"""
