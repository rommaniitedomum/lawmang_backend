import re
from kiwipiepy import Kiwi
from typing import List, Set, Dict
from collections import Counter
import asyncio
from app.chatbot.memory.global_cache import store_template_in_memory
from app.chatbot.tool_agents.tools import async_ES_search_one

kiwi = Kiwi()


def insert_hyperlinks_into_text(text: str, hyperlinks: list) -> str:
    if not hyperlinks:
        return text

    for link in hyperlinks:
        label = link.get("label")
        url = link.get("url")
        tooltip = link.get("tooltip", "")

        if not label or not url:
            continue

        # 🔍 정규식으로 단어 경계만 매칭, 첫 번째 항목만 교체
        pattern = r"\b" + re.escape(label) + r"\b"
        hyperlink_html = f'<a href="{url}" title="{tooltip}">{label}</a>'
        text = re.sub(pattern, hyperlink_html, text, count=1)

    return text


# --------------------------------------------------------------------------------


def extract_json_from_text(text):
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return None


# --------------------------------------------------------------------------------
# 법률 여부 판단 기준: FAISS 키워드 기반
def is_legal_query(keywords: List[str], legal_terms: Set[str], threshold=0.3) -> bool:
    legal_count = sum(1 for kw in keywords if kw in legal_terms)
    ratio = legal_count / len(keywords) if keywords else 0
    return ratio >= threshold


def classify_legal_query(user_input: str, legal_terms: Set[str]) -> str:
    tokens = kiwi.tokenize(user_input)
    extracted = [token.form for token in tokens if token.tag in ("NNG", "NNP")]

    if not extracted:
        return "nonlegal"

    legal_count = sum(1 for word in extracted if word in legal_terms)
    ratio = legal_count / len(extracted)

    return "legal" if ratio >= 0.3 else "nonlegal"


# --------------------------------------------------------------------------------
class faiss_kiwi:
    @staticmethod
    def jaccard_similarity(set1, set2):
        """Jaccard 유사도를 이용한 키워드 비교"""
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if len(union) > 0 else 0

    @staticmethod
    def extract_top_keywords(es_result, top_k=5):
        if isinstance(es_result, dict) and "hits" in es_result:
            blocks = es_result["hits"]
        elif isinstance(es_result, list):
            blocks = es_result
        else:
            # print("⚠️ [extract_top_keywords] 비정상적인 es_result:", es_result)
            return []

        return extract_top_keywords(blocks, top_k=top_k)

    @staticmethod
    def filter_keywords_with_jaccard(user_keywords, faiss_keywords, threshold=0.15):
        """자카드 유사도를 활용하여 FAISS 키워드를 필터링 (유저 키워드 유지)"""
        filtered_keywords = set(user_keywords)  # ✅ 유저 입력 키워드를 무조건 포함

        for faiss_word in faiss_keywords:
            max_sim = max(
                faiss_kiwi.jaccard_similarity(set(faiss_word), set(user_word))
                for user_word in user_keywords
            )
            if max_sim >= threshold:
                filtered_keywords.add(faiss_word)

        return list(filtered_keywords)

    @staticmethod
    def extract_keywords(text: str, top_k: int = 5) -> list[str]:
        """
        주어진 텍스트에서 명사(NNG, NNP) 기반 키워드를 추출합니다.
        """
        tokens = kiwi.tokenize(text)
        nouns = [token.form for token in tokens if token.tag in ("NNG", "NNP")]
        return nouns[:top_k]

    @staticmethod
    def adjust_faiss_keywords(user_input, faiss_keywords):
        """유저 입력 키워드와 FAISS 키워드를 모두 포함하여 검색"""
        user_keywords = faiss_kiwi.extract_keywords(user_input, top_k=5)
        adjusted_keywords = list(set(user_keywords + faiss_keywords))

        # print(f"✅ [최종 검색 키워드]: {adjusted_keywords}")
        return adjusted_keywords

    @staticmethod
    def extract_top_keywords_faiss(user_input, faiss_db, top_k=5):
        """FAISS 검색 후 상위 키워드 추출 (유저 입력 반영)"""
        # print(f"🔍 [FAISS 키워드 추출] 입력: {user_input}")

        search_results = faiss_db.similarity_search(user_input, k=15)
        all_text = " ".join([doc.page_content for doc in search_results])

        faiss_keywords = faiss_kiwi.extract_keywords(all_text, top_k)
        adjusted_keywords = faiss_kiwi.adjust_faiss_keywords(user_input, faiss_keywords)

        # print(f"✅ [FAISS 최종 검색 키워드] {adjusted_keywords}")
        return adjusted_keywords


def validate_model_type(model):
    if not isinstance(model, str):
        raise TypeError(
            f"❌ model 인자는 문자열(str)이어야 합니다. 현재: {type(model)}, 값: {model}"
        )


def extract_top_keywords(text_blocks: list[dict], top_k=5) -> list[str]:
    """
    Elasticsearch 결과 중 question/answer에서 가장 자주 등장하는 명사 기반 상위 키워드 추출
    """
    all_text = " ".join(
        block.get("question", "") + " " + block.get("answer", "")
        for block in text_blocks
    )

    # 한글/영문 단어 추출
    tokens = re.findall(r"[가-힣a-zA-Z]{2,}", all_text)

    # 상위 빈도 단어 추출
    counter = Counter(tokens)
    top_keywords = [word for word, _ in counter.most_common(top_k)]

    return top_keywords


# ------------------------------------------------------------------


async def update_llm2_template_with_es(template_data: Dict, user_query: str) -> None:
    template = template_data.get("template", {}) or {}
    strategy = template_data.get("strategy", {}) or {}
    precedent = template_data.get("precedent", {}) or {}

    async def get_keywords_from_texts(texts, top_k=5):
        es_result = await async_ES_search_one(texts)
        hits = es_result.get("hits", [])
        return extract_top_keywords(hits, top_k=top_k) or ["기본"]

    # 1. Summary용 키워드
    summary_keywords = await get_keywords_from_texts(
        [user_query, template.get("summary", "")]
    )
    template["summary"] = "updated.summary.from.es: " + ", ".join(summary_keywords)

    # 2. Explanation
    explanation_keywords = await get_keywords_from_texts(
        [template.get("explanation", ""), strategy.get("final_strategy_summary", "")]
    )
    template["explanation"] = "updated.explanation.from.es: " + ", ".join(
        explanation_keywords
    )

    # 3. Ref question
    ref_keywords = await get_keywords_from_texts([template.get("ref_question", "")])
    template["ref_question"] = "updated.ref_question.from.es: " + ", ".join(
        ref_keywords
    )

    # 4. Strategy summary
    strat_keywords = await get_keywords_from_texts(
        [
            strategy.get("final_strategy_summary", ""),
            " ".join(strategy.get("decision_tree", [])),
        ]
    )
    strategy["final_strategy_summary"] = "updated.strategy.from.es: " + ", ".join(
        strat_keywords
    )
    strategy["decision_tree"] = [
        f"사용자가 '{kw}' 관련 질문을 하면 법적 요건을 중심으로 판단"
        for kw in strat_keywords
    ]

    # 5. Precedent
    prec_keywords = await get_keywords_from_texts(
        [precedent.get("summary", ""), precedent.get("title", "")]
    )
    precedent["summary"] = "updated.precedent.from.es: " + ", ".join(prec_keywords)
    precedent["title"] = f"{prec_keywords[0]} 관련 증강 판례"

    store_template_in_memory(
        {
            "built": True,
            "built_by_llm2": True,
            "updated_by_es": True,
            "template": template,
            "strategy": strategy,
            "precedent": precedent,
        }
    )


async def evalandsave_llm2_template_with_es(
    template_data: Dict, user_query: str
) -> None:
    template = template_data.get("template", {}) or {}
    strategy = template_data.get("strategy", {}) or {}
    precedent = template_data.get("precedent", {}) or {}

    async def get_keywords_and_score(texts, top_k=5):
        es_result = await async_ES_search_one(texts)
        hits = es_result.get("hits", [])
        max_score = es_result.get("max_score", 0)
        return extract_top_keywords(hits, top_k=top_k) or ["기본"], max_score

    # ✅ 1. Summary용 키워드 + 점수
    summary_keywords, summary_score = await get_keywords_and_score(
        [user_query, template.get("summary", "")]
    )
    updated_summary = "updated.summary.from.es: " + ", ".join(summary_keywords)
    template["summary"] = updated_summary
    template["summary_raw"] = template.get("summary", "")  # 원문 보존
    template["summary_score"] = summary_score

    # ✅ 2. Explanation
    explanation_keywords, explanation_score = await get_keywords_and_score(
        [template.get("explanation", ""), strategy.get("final_strategy_summary", "")]
    )
    updated_explanation = "updated.explanation.from.es: " + ", ".join(
        explanation_keywords
    )
    template["explanation"] = updated_explanation
    template["explanation_raw"] = template.get("explanation", "")
    template["explanation_score"] = explanation_score

    # ✅ 3. Ref question
    ref_keywords, ref_score = await get_keywords_and_score(
        [template.get("ref_question", "")]
    )
    updated_ref_question = "updated.ref_question.from.es: " + ", ".join(ref_keywords)
    template["ref_question"] = updated_ref_question
    template["ref_question_raw"] = template.get("ref_question", "")
    template["ref_question_score"] = ref_score

    # ✅ 4. Strategy summary
    strat_keywords, _ = await get_keywords_and_score(
        [
            strategy.get("final_strategy_summary", ""),
            " ".join(strategy.get("decision_tree", [])),
        ]
    )
    strategy["final_strategy_summary"] = "updated.strategy.from.es: " + ", ".join(
        strat_keywords
    )
    strategy["decision_tree"] = [
        f"사용자가 '{kw}' 관련 질문을 하면 법적 요건을 중심으로 판단"
        for kw in strat_keywords
    ]

    # ✅ 5. Precedent
    prec_keywords, _ = await get_keywords_and_score(
        [precedent.get("summary", ""), precedent.get("title", "")]
    )
    precedent["summary"] = "updated.precedent.from.es: " + ", ".join(prec_keywords)
    precedent["title"] = f"{prec_keywords[0]} 관련 증강 판례"

    # ✅ 캐시 저장
    store_template_in_memory(
        {
            "built": True,
            "built_by_llm2": True,
            "updated_by_es": True,
            "template": template,
            "strategy": strategy,
            "precedent": precedent,
        }
    )


def calculate_llm2_accuracy_score(template_score: float, user_score: float) -> int:
    """
    사용자 점수(user_score)는 보조 신호로만 사용하고,
    template_score를 중심으로 10~100 스케일의 정확도를 계산.
    """
    if not template_score or not user_score:
        return 0

    # 1. 템플릿 점수 정규화 (10~100 사이 값 기준)
    template_scaled = min(max(template_score, 10), 100)

    # 2. 사용자 점수 가중치 적용 (10~25 범위 → 0.0 ~ 1.0)
    user_weight = (user_score - 10) / 15  # → 0.0 ~ 1.0

    # 3. 정확도 계산 (template 중심, user는 최대 10점 가산)
    final_score = template_scaled + (10 * user_weight)

    return min(100, int(final_score))
