from typing import List, Literal
from app.deepresearch.core.gpt_engine import llm_call
from app.deepresearch.prompts.system_prompt import system_prompt
from app.deepresearch.prompts.report_prompts import generate_legal_prompt, generate_tax_prompt

def write_final_report(
    prompt: str,
    learnings: List[str],
    visited_urls: List[str],
    client,
    model: str,
    report_type: Literal["legal", "tax"] = "legal",
) -> str:
    """모든 연구 결과를 바탕으로 최종 보고서를 생성합니다."""
    learnings_string = "\n".join([f"({i+1}) {learning}" 
                                 for i, learning in enumerate(learnings)])[:150000]

    # 프롬프트 선택
    if report_type == "legal":
        user_prompt = generate_legal_prompt(prompt, learnings_string)
    else:
        user_prompt = generate_tax_prompt(prompt, learnings_string)

    sys_prompt = system_prompt()
    if sys_prompt:
        user_prompt = f"{sys_prompt}\n\n{user_prompt}"

    try:
        report = llm_call(
            user_prompt,
            model,
            client,
            max_tokens=3500,
            temperature=0.2
        )

        urls_section = ""
        if visited_urls:
            urls_section = "\n\n참고 출처:\n" + "\n".join(
                f"({i+1}) {url}" for i, url in enumerate(visited_urls)
            )

        notice = ("\n\n⚠️ 본 리포트는 참고용입니다. "
                 f"복잡한 {report_type}문제는 전문가 상담을 권장합니다.")

        return report.strip() + urls_section + notice

    except Exception as e:
        error_msg = f"❌ 보고서 생성 중 오류 발생: {e}"
        print(error_msg)
        return error_msg
    