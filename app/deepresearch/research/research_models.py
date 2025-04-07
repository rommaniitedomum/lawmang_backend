from typing import List
from pydantic import BaseModel

class SearchResult(BaseModel):
    url: str
    markdown: str
    description: str
    title: str

class SerpQuery(BaseModel):
    query: str
    research_goal: str

class SerpQueryResponse(BaseModel):
    queries: List[SerpQuery]

class SerpResultResponse(BaseModel):
    learnings: List[str]
    followUpQuestions: List[str]

class ResearchResult(BaseModel):
    learnings: List[str]
    visited_urls: List[str]
