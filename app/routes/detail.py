from fastapi import APIRouter, HTTPException
from app.core.database import execute_sql
from langchain_openai import ChatOpenAI
import os
from app.services.precedent_detail_service import fetch_external_precedent_detail
from app.services.consultation_detail_service import get_consultation_detail_by_id
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()

# ✅ API 호출 시점에 OpenAI 객체 생성 (런타임 오류 방지)
def get_openai_llm():
    return ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=OPENAI_API_KEY)


# ✅ 판례 상세 정보 조회
@router.get("/precedent/{pre_number}")
async def fetch_precedent_detail(pre_number: int):
    try:
        detail = await fetch_external_precedent_detail(pre_number)
        return detail
    except HTTPException as e:
        # 서비스에서 발생한 HTTPException은 그대로 전달
        raise e


# ✅ 상담 상세 정보 조회
@router.get("/consultation/{consultation_id}")
def fetch_consultation_detail(consultation_id: int):
    try:
        detail = get_consultation_detail_by_id(consultation_id)
        return detail
    except HTTPException as e:
        # 서비스에서 발생한 HTTPException은 그대로 전달
        raise e


# ✅ 판례 요약 생성 API
@router.get("/precedent/summary/{pre_number}")
async def get_precedent_summary(pre_number: int):
    """판례 번호를 받아 해당 판례의 요약을 반환하는 API"""

    if pre_number <= 0:
        raise HTTPException(status_code=400, detail="유효하지 않은 판례 번호입니다.")

    try:
        # ✅ 외부 API를 호출하여 판례 원문 가져오기
        precedent_text = await fetch_external_precedent_detail(pre_number)

        if not precedent_text:
            raise HTTPException(status_code=404, detail="판례 내용을 찾을 수 없습니다.")

        # ✅ 판결 요약을 위한 프롬프트 생성
        summary_prompt = """
        다음은 법원의 판결문입니다. 주어진 내용을 기반으로 판례의 핵심 내용을 요약해주세요.

        **요약 조건**
        - 사건 개요, 판결 과정, 판결 요약 순으로 정리할 것
        - 핵심 판결 이유와 법원이 적용한 법 조항을 포함할 것
        - 법원의 판단이 바뀐 주요 이유를 명확히 설명할 것
        - 문장의 어미를 최대한 줄여서 통일할 것

        **출력 예시**
        【 사건 개요 】 피고인은 '사건 개요 요약' 혐의로 기소됨.

        【 판결 과정 】 법원은 '판결 과정'을 근거로 판결을 내림.

        【 판결 요약 】 이 사건은 '핵심 판결 내용 및 적용 법리'에 대한 판결로, 최종적으로 '주요 판결 결과'가 내려짐.

        **판례 원문**
        {precedent_text}
        """

        # ✅ 최종 프롬프트 완성
        summary_prompt = summary_prompt.format(precedent_text=precedent_text)

        # ✅ OpenAI API 호출
        llm = get_openai_llm()
        summary = str(llm.invoke(summary_prompt).content)

        # ✅ 개행 처리 개선
        summary = summary.replace(". -", ".\n\n- ")  # 리스트 항목 개행 적용
        summary = summary.replace("판시함.", "판시함.\n\n")  # 법적 판단 개행 적용
        summary = summary.replace(". ", ".\n")  # 문장 끝 개행 추가

        return {"pre_number": pre_number, "summary": summary}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail="판례 요약을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.")
