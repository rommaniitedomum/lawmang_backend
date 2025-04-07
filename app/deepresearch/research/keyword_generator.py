from typing import List, Optional
from app.deepresearch.research.research_models import SerpQueryResponse, SerpQuery
from app.deepresearch.core.gpt_engine import JSON_llm
from app.deepresearch.prompts.system_prompt import system_prompt

def generate_serp_queries(
    query: str,
    client,
    model: str,
    num_queries: int = 2,
    learnings: Optional[List[str]] = None
) -> List[SerpQuery]:
    """
    사용자의 입력을 바탕으로 검색 쿼리를 생성합니다. (동기 버전)
    """
    prompt = f"""
    다음 사용자 입력을 기반으로, 사용자가 겪고 있는 소송 또는 세무 신고 상황에 대해 다음 정보를 조사할 수 있도록 검색 쿼리를 생성하세요.
    - 사건 또는 신고 상황의 주요 쟁점은 무엇인지
    - 실수하거나 대응하지 않았을 때 생길 수 있는 불이익
    - 실무에서 참고할 수 있는 실제 사례
    - 사건 해결 또는 신고 성공을 위한 대응 전략

    JSON 객체를 반환하며, 'queries' 배열 필드에 {num_queries}개의 검색 쿼리를 포함해야 합니다.
    각 쿼리 객체에는 'query'와 'research_goal' 필드가 포함되어야 하며, 각 쿼리는 고유해야 합니다.
    <입력>{query}</입력>
    """

    if learnings:
        prompt += f"\n\n이전 학습 내용: {' '.join(learnings)}"

    system_msg = system_prompt()

    def call_llm():
        response_json = JSON_llm(prompt, SerpQueryResponse, client, system_msg, model)
        try:
            result = SerpQueryResponse.model_validate(response_json)
            return result.queries[:num_queries]
        except Exception as e:
            print(f"generate_serp_queries 오류: {e}")
            return []

    return call_llm()
