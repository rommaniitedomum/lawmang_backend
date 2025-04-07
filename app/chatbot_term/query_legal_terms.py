from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

# 벡터 저장 위치
DB_FAISS_PATH = "./app/chatbot_term/vectorstore"

# 벡터 DB 로드
embedding = OpenAIEmbeddings()
db = FAISS.load_local(DB_FAISS_PATH, embedding, allow_dangerous_deserialization=True)
retriever = db.as_retriever(search_kwargs={"k": 10})

# 프롬프트 템플릿
template = """당신은 법률 분야에 전문적인 지식을 가진 AI 어시스턴트입니다.

사용자가 특정 법률 용어나 개념을 입력하면,  
먼저 **청소년도 이해할 수 있는 쉬운 말**로 간단하고 명확하게 설명해주세요.  
**말투는 반드시 격식 있는 문어체(~입니다, ~합니다)를 사용하고,  
구어체(~해요, ~있어요)는 절대 사용하지 마세요.**

설명은 핵심 내용을 중심으로 구성하며,  
불필요하게 다른 개념을 덧붙이지 마세요.

※ 유사한 용어가 함께 검색되더라도,  
사용자가 질문한 **용어 자체의 의미를 가장 먼저 중심적으로 설명**해주세요.

같은 용어라도 사건의 종류(형사소송, 민사소송 등)에 따라 의미가 달라질 수 있습니다.  
category 정보가 다르면 각각 구분해서 설명해주세요.

용어: {question}

RAG 검색 결과:  
{context}
"""

QA_PROMPT = PromptTemplate(input_variables=["question", "context"], template=template)
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# ✅ LLMChain 대체
qa_chain = QA_PROMPT | llm

# ✅ 최종 함수
def get_legal_term_answer(query: str) -> str:
    try:
        # 문서 검색
        docs = retriever.get_relevant_documents(query)

        exact_match = None
        partial_matches = []

        for doc in docs:
            metadata = doc.metadata or {}
            term = metadata.get("term", "").strip()

            if query.strip() == term:
                exact_match = doc
                break

            if query.strip() in term:
                partial_matches.append(doc)

        selected = None
        if exact_match:
            selected = exact_match
        elif partial_matches:
            partial_matches.sort(key=lambda d: len(d.metadata.get("term", "")))
            selected = partial_matches[0]

        # GPT fallback
        if not selected:
            gpt_result = qa_chain.invoke({"question": query, "context": ""})
            return f"※ 아래 설명은 GPT가 자체적으로 생성한 추론 결과입니다.\n\n{gpt_result.content}"

        context = selected.page_content.strip()
        return qa_chain.invoke({"question": query, "context": context}).content

    except Exception as e:
        print(f"[ERROR] get_legal_term_answer 실패: {e}")
        return "죄송합니다. 예상치 못한 오류가 발생했습니다."