import os
import json
import sys
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.chatbot.tool_agents.tools import LawGoKRTavilySearch
from app.chatbot.tool_agents.utils.utils import (
    insert_hyperlinks_into_text,
)
from langchain.memory import ConversationBufferMemory
from langchain_teddynote import logging

logging.langsmith("llamaproject")

# ✅ LangChain ChatOpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

memory = ConversationBufferMemory(
    memory_key="chat_history", max_token_limit=1000, return_messages=True
)


def build_final_answer_prompt(
    template: dict, strategy: dict, precedent: dict, user_query: str
) -> str:
    precedent_summary = precedent.get("summary", "")
    precedent_link = precedent.get("casenote_url", "")
    precedent_meta = f"{precedent.get('court', '')} / {precedent.get('j_date', '')} / {precedent.get('title', '')}"

    summary_with_links = insert_hyperlinks_into_text(
        template["summary"], template.get("hyperlinks", [])
    )
    explanation_with_links = insert_hyperlinks_into_text(
        template["explanation"], template.get("hyperlinks", [])
    )
    hyperlinks_text = "\n".join(
        [f"- {link['label']}: {link['url']}" for link in template.get("hyperlinks", [])]
    )
    strategy_decision_tree = "\n".join(strategy.get("decision_tree", []))

    chat_history = memory.load_memory_variables({}).get("chat_history", "")

    prompt = f"""
당신은 법률 상담을 생성하는 고급 AI입니다.

[대화 히스토리]
{chat_history}

[사용자 질문]
{user_query}

[요약]
{summary_with_links}

[설명]
{explanation_with_links}

[참고 질문]
{template["ref_question"]}

[하이퍼링크]
{hyperlinks_text}

[전략 요약]
{strategy.get("final_strategy_summary", "")}

[응답 구성 전략]
- 말투: {strategy.get("tone", "")}
- 흐름: {strategy.get("structure", "")}
- 조건 흐름도:
{strategy_decision_tree}

[추천 링크]
{json.dumps(strategy.get("recommended_links", []), ensure_ascii=False)}

[추가된 판례 요약]
- {precedent_summary}
- 링크: {precedent_link}
- 정보: {precedent_meta}

💡 위 내용을 반영하여, 사용자가 신뢰할 수 있는 법률 상담을 생성하세요.
"""
    return prompt.strip()


def run_final_answer_generation(
    template: dict,
    strategy: dict,
    precedent: dict,
    user_query: str,
    model: str = "gpt-4",
) -> str:
    final_prompt = build_final_answer_prompt(template, strategy, precedent, user_query)
    print("\n🤖 AI 답변:")
    final_answer = ""

    # ✅ LangChain ChatOpenAI (Streaming)
    llm = ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        temperature=0.4,
        streaming=True
    )

    messages = [
        SystemMessage(
            content="당신은 고급 법률 응답을 생성하는 AI입니다. 사용자의 신뢰를 얻을 수 있는 정확하고 자연스러운 상담을 생성하세요."
        ),
        HumanMessage(content=final_prompt),
    ]

    # ✅ 스트리밍 응답 처리
    for chunk in llm.stream(messages):
        if hasattr(chunk, "content") and chunk.content:
            sys.stdout.write(chunk.content)
            sys.stdout.flush()
            final_answer += chunk.content

    # ✅ 메모리에 저장
    memory.save_context(
        {"user_query": user_query}, {"response": precedent.get("summary", "")}
    )

    return final_answer
