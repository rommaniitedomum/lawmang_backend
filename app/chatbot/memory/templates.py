# JSON 형식으로 저장된 default templates 파일 생성
import os
import json

def get_default_strategy_template() -> dict:
    """
    📌 전략 생성 실패 시 또는 초기값으로 사용할 기본 전략 템플릿 반환
    """
    return {
        "tone": "",
        "structure": "",
        "decision_tree": [],
        "final_strategy_summary": "",
        "recommended_links": [],
        "evaluation": {
            "needs_revision": False,
            "reason": "",
            "tavily_snippets": [],
        },
        "explanation": "",
    }
def get_default_response_template() -> dict:
    """
    📌 응답 템플릿 생성 실패 시 사용할 기본 템플릿 반환
    """
    return {
        "summary": "",
        "explanation": "",
        "hyperlinks": [],
        "ref_question": "",
    }


templates_json = {
    "DEFAULT_STRATEGY_TEMPLATE": {
        "tone": "",
        "structure": "",
        "decision_tree": [],
        "final_strategy_summary": "",
        "recommended_links": [],
        "evaluation": {"needs_revision": False, "reason": "", "tavily_snippets": []},
        "explanation": "",
    },
    "DEFAULT_RESPONSE_TEMPLATE": {
        "summary": "",
        "explanation": "",
        "hyperlinks": [],
        "ref_question": "",
    },
}

json_path = "app/chatbot/memory/templates.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(templates_json, f, ensure_ascii=False, indent=2)

json_path