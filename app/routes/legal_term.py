from fastapi import APIRouter
from pydantic import BaseModel
from app.chatbot_term.query_legal_terms import get_legal_term_answer

router = APIRouter()

class LegalTermRequest(BaseModel):
    question: str

@router.post("/legal-term")
async def get_legal_term_response(req: LegalTermRequest):
    result = get_legal_term_answer(req.question)
    return {"result": result}
