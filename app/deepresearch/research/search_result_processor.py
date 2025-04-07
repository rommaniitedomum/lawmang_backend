from typing import List, Dict
from app.deepresearch.research.research_models import SearchResult, SerpResultResponse
from app.deepresearch.core.gpt_engine import JSON_llm
from app.deepresearch.prompts.system_prompt import system_prompt


def process_serp_result(
    query: str,
    search_result: List[SearchResult],
    client,
    model: str,
    num_learnings: int = 3
) -> Dict[str, List[str]]:
    """
    검색 결과를 바탕으로 학습 내용과 후속 질문을 추출합니다.
    """
    contents = [item.markdown.strip()[:10000] for item in search_result if item.markdown]
    contents_str = "".join(f"<내용>\n{content}\n</내용>" for content in contents)

    prompt = f"""
    <쿼리>{query}</쿼리>에 대한 검색 결과입니다.
    아래 내용을 바탕으로, 사용자의 소송/분쟁 또는 세무 신고 상황과 관련된 핵심 정보를 최대 {num_learnings}개 추출하세요.

    반환 형식은 반드시 아래 JSON 형식을 따르세요:
    {{
        "learnings": ["...", "...", "..."],
        "followUpQuestions": ["...", "..."]
    }}

    - 각 항목은 짧고 명확한 문장으로 작성되어야 하며
    - 마크다운이나 설명 없이 JSON만 반환하세요.
    - learnings에는 핵심 쟁점, 사례, 전략이 포함되어야 하고
    - followUpQuestions에는 사용자가 더 알고 싶어할 만한 후속 질문을 포함하세요.

    <검색 결과>{contents_str}</검색 결과>
    """

    system_msg = system_prompt()

    response_json = JSON_llm(prompt, SerpResultResponse, client, system_msg, model)

    try:
        result = SerpResultResponse.model_validate(response_json)
        return {
            "learnings": list(set(result.learnings)),
            "followUpQuestions": result.followUpQuestions
        }
    except Exception as e:
        print(f"process_serp_result 오류: {e}")
        return {"learnings": [], "followUpQuestions": []}
