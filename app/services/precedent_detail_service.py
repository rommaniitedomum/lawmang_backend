import httpx
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

async def fetch_external_precedent_detail(pre_number: int):
    """
    1. JSON 요청을 먼저 보냄.
    2. JSON 응답의 최상위 키를 확인:
       - "PrecService"가 있으면 JSON 반환
       - "Law"가 있으면 HTML API 요청 후 HTML 반환
    """
    if not pre_number or pre_number <= 0:
        raise HTTPException(status_code=400, detail="유효하지 않은 판례 번호입니다.")

    json_api_url = f"https://www.law.go.kr/DRF/lawService.do?OC=youngsunyi&target=prec&ID={pre_number}&type=JSON"
    html_api_url = f"https://www.law.go.kr/DRF/lawService.do?OC=youngsunyi&target=prec&ID={pre_number}&type=HTML"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(json_api_url)
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"외부 API 요청 실패: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"외부 API 호출 실패: {response.text}")

    try:
        data = response.json()

        # ✅ 최상위 키 확인
        first_key = next(iter(data))  # 첫 번째 키 가져오기
        if first_key == "PrecService":
            return data["PrecService"]  # ✅ 정상 JSON 반환

        elif first_key == "Law":
            # ✅ "Law" 키가 있으면 HTML 요청 후 반환
            async with httpx.AsyncClient(timeout=10) as client:
                html_response = await client.get(html_api_url)

            if html_response.status_code != 200:
                raise HTTPException(status_code=html_response.status_code, detail="HTML API 호출 실패")

            return HTMLResponse(content=html_response.text)

        raise HTTPException(status_code=500, detail="예상치 못한 JSON 응답 형식입니다.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON 응답 파싱 오류: {str(e)}")