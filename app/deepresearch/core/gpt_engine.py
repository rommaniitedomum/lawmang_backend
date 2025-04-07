from typing import Optional
from pydantic import BaseModel
import re

def llm_call(prompt: str, model: str, client, max_tokens: int = 1000, temperature: float = 0.2) -> str:
    """
    주어진 프롬프트로 LLM을 동기적으로 호출합니다.
    이는 메시지를 하나의 프롬프트로 연결하는 일반적인 헬퍼 함수입니다.
    """
    messages = [{"role": "user", "content": prompt}]
    chat_completion = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    # print(model, "완료")
    return chat_completion.choices[0].message.content

def clean_json_block(text: str) -> str:
    # 마크다운 블록 제거 (```json ... ``` 포함)
    return re.sub(r"^```(?:json)?\n|\n```$", "", text.strip())

def JSON_llm(user_prompt: str, schema: BaseModel, client, system_prompt: Optional[str] = None, model: Optional[str] = None):
    # print(f"[DEBUG] JSON_llm 내부 model: {model}")
    # print(f"[DEBUG] client 타입: {type(client)}")

    if model is None:
        model = "gpt-4o-mini"

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2
        )

        raw_text = response.choices[0].message.content
        # print(f"[DEBUG] raw_text: {raw_text}")

        # 마크다운 블럭 제거
        cleaned = re.sub(r"```(?:json)?\n|```", "", raw_text.strip())
        # print(f"[DEBUG] cleaned: {cleaned}")

        return schema.model_validate_json(cleaned)

    except Exception as e:
        print(f"Error in JSON_llm (manual parsing): {e}")
        return None
