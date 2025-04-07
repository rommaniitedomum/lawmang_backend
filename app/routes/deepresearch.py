from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from openai import OpenAI
from app.deepresearch.research.deep_research import deep_research
from app.deepresearch.reporting.report_builder import write_final_report
import os
from datetime import datetime

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()

class LegalCase(BaseModel):
    case_type: str = Field(..., description="소송 또는 분쟁의 유형")
    incident_date: str = Field(..., description="사건 발생 시점")
    related_party: str = Field(..., description="사건 상대방")
    fact_details: str = Field(..., description="사실관계 요약")
    evidence: str = Field(..., description="확보한 증거")
    prior_action: str = Field(..., description="기존 대응 여부")
    desired_result: str = Field(..., description="원하는 해결 결과")

class TaxCase(BaseModel):
    report_type: str = Field(..., description="세금 신고 유형")
    report_period: str = Field(..., description="신고 대상 기간")
    income_type: str = Field(..., description="소득 또는 사업 유형")
    concern: str = Field(..., description="걱정되는 점")
    desired_result: str = Field(..., description="원하는 신고 목표")
    additional_info: str | None = Field(default=None, description="추가 상황 또는 참고 사항")

class ResearchResponse(BaseModel):
    combined_query: str
    research_results: dict
    final_report: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_type: str

@router.post("/structured-research/legal", response_model=ResearchResponse)
async def structured_research_legal(
    case: LegalCase,
    client: OpenAI = Depends(get_openai_client)
):
    try:
        prompt = (
            f"[사건유형] {case.case_type}\n"
            f"[사건시점] {case.incident_date}\n"
            f"[관련자] {case.related_party}\n"
            f"[사실관계]\n{case.fact_details}\n\n"
            f"[증거] {case.evidence}\n"
            f"[대응여부] {case.prior_action}\n"
            f"[바람] {case.desired_result}"
        )

        research_results = deep_research(
            query=prompt,
            breadth=2,
            depth=1,
            client=client,
            model="gpt-4o-mini"
        )

        final_report = write_final_report(
            prompt=prompt,
            learnings=research_results.learnings,
            visited_urls=research_results.visited_urls,
            client=client,
            model="gpt-4o-mini",
            report_type="legal"
        )

        return ResearchResponse(
            combined_query=prompt,
            research_results=research_results.model_dump(),
            final_report=final_report,
            report_type="legal"
        )

    except Exception as e:
        print(f"🔥 서버 내부 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/structured-research/tax", response_model=ResearchResponse)
async def structured_research_tax(
    case: TaxCase,
    client: OpenAI = Depends(get_openai_client)
):
    try:
        # additional_info가 None인 경우 빈 문자열로 처리
        additional_info = case.additional_info or ""
        
        prompt = (
            f"[신고유형] {case.report_type}\n"
            f"[신고대상기간] {case.report_period}\n"
            f"[소득유형] {case.income_type}\n"
            f"[걱정되는점] {case.concern}\n"
            f"[바라는점] {case.desired_result}\n"
            f"[기타상황] {additional_info}"
        )

        research_results = deep_research(
            query=prompt,
            breadth=2,
            depth=1,
            client=client,
            model="gpt-4o-mini"
        )

        final_report = write_final_report(
            prompt=prompt,
            learnings=research_results.learnings,
            visited_urls=research_results.visited_urls,
            client=client,
            model="gpt-4o-mini",
            report_type="tax"
        )

        return ResearchResponse(
            combined_query=prompt,
            research_results=research_results.model_dump(),
            final_report=final_report,
            report_type="tax"
        )

    except Exception as e:
        print(f"🔥 서버 내부 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))
