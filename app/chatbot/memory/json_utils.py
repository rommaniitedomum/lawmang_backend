import json
import os
from asyncio import Lock

json_lock = Lock()
JSON_PATH = "app/chatbot/memory/yes_counter.json"


async def read_json():
    if not os.path.exists(JSON_PATH):
        return {"yes_count": 0, "escalated": False}
    async with json_lock:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            return json.load(file)


async def write_json(data):
    async with json_lock:
        with open(JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)


async def increment_yes_count():
    data = await read_json()
    data["yes_count"] += 1
    if data["yes_count"] >= 3:
        data["escalated"] = True
        data["yes_count"] = 0  # 초기화
    await write_json(data)
    return data["escalated"]


async def reset_yes_count():
    await write_json({"yes_count": 0, "escalated": False})
