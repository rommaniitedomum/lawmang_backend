from typing import Literal
from app.deepresearch.core.firecrawl_client import FirecrawlClient
from app.deepresearch.research.research_models import ResearchResult, SearchResult
from app.deepresearch.research.keyword_generator import generate_serp_queries
from app.deepresearch.research.search_result_processor import process_serp_result


def deep_research(
    query: str,
    breadth: int = 2,
    depth: int = 1,
    client = None,
    model: str = "gpt-4o-mini",
    search_type: Literal["legal", "tax"] = "legal"
) -> ResearchResult:
    """
    주어진 쿼리에 대해 다단계 리서치를 수행합니다. (동기 버전)
    breadth: 생성할 쿼리 수, depth: 각 쿼리에 대해 반복 횟수
    """
    try:
        crawler = FirecrawlClient(search_type=search_type)

        all_learnings = []
        all_urls = []

        # Step 1. 관련 검색 쿼리 생성
        serp_queries = generate_serp_queries(
            query=query,
            client=client,
            model=model,
            num_queries=breadth
        )

        for serp in serp_queries:
            # Step 2. 검색 수행
            search_results = crawler.search(serp.query)

            # Step 3. 결과 정제
            processed = crawler.process_results(search_results)

            # Step 4. 컨텐츠 추출
            search_result_objects = []
            for item in processed:
                url = item["url"]
                content = item.get("markdown", "")  # ✅ markdown은 이미 포함되어 있음
                search_result_objects.append(SearchResult(
                    url=url,
                    title=item.get("title", ""),
                    description=item.get("snippet", ""),
                    markdown=content
                ))
                all_urls.append(url)

            # Step 5. 학습 추출
            serp_output = process_serp_result(
                query=serp.query,
                search_result=search_result_objects,
                client=client,
                model=model
            )
            all_learnings.extend(serp_output.get("learnings", []))

        # print("[DEBUG] 최종 결과 learnings:")
        # print(all_learnings)
        # print("[DEBUG] 최종 결과 visited_urls:")
        # print(all_urls)

        return ResearchResult(
            learnings=list(set(all_learnings)),
            visited_urls=list(set(all_urls))
        )

    except Exception as e:
        print(f"심층 리서치 중 오류 발생: {e}")
        return ResearchResult(learnings=[], visited_urls=[])
