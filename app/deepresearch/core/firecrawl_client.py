import os
from typing import List, Optional, Dict, Literal
from firecrawl import FirecrawlApp
from app.deepresearch.research.research_models import SearchResult
from urllib.parse import urlparse

# 법률 관련 신뢰할 수 있는 도메인
LEGAL_DOMAINS = [
    "law.go.kr",
    "www.moef.go.kr",
    "www.lawnb.com",
]

# 세무/회계 관련 신뢰할 수 있는 도메인
TAX_DOMAINS = [
    "hometax.go.kr",
    "nts.go.kr",
    "www.simpan.go.kr",
    "www.kacpta.or.kr",
    "www.kicpa.or.kr",
    "www.koreatax.org",
    "www.taxnet.co.kr",
    "www.etaxkorea.net",
    "www.taxguide.co.kr",
    "www.taxpoint.co.kr",
    "www.taxkorea.net",
    "www.taxrefund.co.kr",
    "www.taxconsulting.co.kr",
    "www.taxaccount.co.kr",
    "www.taxnews.co.kr",
]

TRUSTED_DOMAINS = [*LEGAL_DOMAINS, *TAX_DOMAINS]

class FirecrawlClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_type: Literal["legal", "tax"] = "legal"
    ):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.search_type = search_type
        self.trusted_domains = LEGAL_DOMAINS if search_type == "legal" else TAX_DOMAINS
        self.app = FirecrawlApp(api_key=self.api_key)

    def _is_trusted_domain(self, url: str) -> bool:
        try:
            domain = urlparse(url).netloc
            return any(trusted in domain for trusted in self.trusted_domains)
        except:
            return False

    def search(self, query: str, timeout: int = 15000, limit: int = 5) -> List[Dict]:
        try:
            response = self.app.search(
                query=query,
                params={
                    "timeout": timeout,
                    "limit": limit,
                    "scrapeOptions": {"formats": ["markdown"]}
                }
            )
            return response.get("data", [])
        except Exception as e:
            print(f"🔥 Firecrawl 검색 오류: {e}")
            return []

    def get_content(self, url: str) -> str:
        # Firecrawl SDK에는 scrape 기능이 없으므로 이 함수는 빈 문자열 반환
        return ""

    def process_results(self, results: List[Dict]) -> List[Dict]:
        processed_results = []
        for result in results:
            url = result.get("url", "")
            if not self._is_trusted_domain(url):
                continue
            try:
                processed_result = {
                    "url": url,
                    "title": result.get("title", "").strip(),
                    "snippet": result.get("snippet", "").strip(),
                    "source": self.search_type,
                    "timestamp": result.get("timestamp"),
                    "markdown": result.get("markdown", "")  # ✅ 검색 결과에 이미 markdown 포함
                }
                processed_results.append(processed_result)
            except Exception as e:
                print(f"결과 처리 중 오류 발생: {e}")
                continue
        return processed_results