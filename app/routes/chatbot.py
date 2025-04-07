from pydantic import BaseModel # 데이터 모델 타입 정의 모듈
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from dotenv import load_dotenv
from app.chatbot.agent import process_query
import os

# 환경 변수 설정
load_dotenv()

router = APIRouter()

# 대화 기록을 저장할 전역 변수
conversation_history = []

class ChatMessage(BaseModel):
  role: str
  parts: List[Dict[str, str]]
  
class ChatRequest(BaseModel):
  contents: str
  
class ChatCandidate(BaseModel):
  content: ChatMessage
  
class ChatResponse(BaseModel):
  candidates: List[ChatCandidate]
  mcq_question: str | None = None
  yes_count: int = 0
  

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
  """
  법률 질문에 답변해 드립니다. - 법률 상담 챗봇
	"""
  try:
    # 현재 사용자의 입력 메시지 가져오기
    current_message = request.contents
    
    # AI 응답 생성
    response = await process_query(current_message, conversation_history)
    # print(response)
    
    # 대화 기록에 현재 대화 추가
    conversation_history.append({
        "user": current_message,
        "assistant": response
    })
    
    # ChatResponse 형식에 맞게 응답 반환
    return ChatResponse(
        candidates=[
            ChatCandidate(
                content=ChatMessage(
                    role="model",
                    parts=[{"text": response}]
                )
            )
        ],
        mcq_question=response,
        yes_count=0
    )
    
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")
  
@router.post("/reset")
async def reset_conversation():
  """
  대화 기록 초기화
  """
  conversation_history.clear()
  return {"message": "대화 기록이 초기화되었습니다."}