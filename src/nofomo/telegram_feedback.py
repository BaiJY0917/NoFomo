import json
import re
from pathlib import Path

import requests

COMMAND_PATTERN = re.compile(r"^/(like|dislike)\s+([A-Za-z0-9_-]+)$")


def extract_feedback_command(update: dict) -> dict | None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    match = COMMAND_PATTERN.match(text)
    from_user = message.get("from") or {}
    chat = message.get("chat") or {}
    update_id = update.get("update_id")
    message_id = message.get("message_id")
    telegram_user_id = from_user.get("id")
    telegram_chat_id = chat.get("id")
    if not match:
        return None
    if update_id is None or message_id is None or telegram_user_id is None or telegram_chat_id is None:
        return None
    return {
        "update_id": update_id,
        "feedback_type": match.group(1),
        "item_id": match.group(2),
        "telegram_user_id": telegram_user_id,
        "telegram_chat_id": telegram_chat_id,
        "telegram_message_id": message_id,
        "created_at": message.get("date"),
    }


def load_offset(path: Path) -> int | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("offset")


def save_offset(path: Path, offset: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"offset": offset}, ensure_ascii=False, indent=2), encoding="utf-8")


def next_offset(update_id: int) -> int:
    return update_id + 1


def fetch_updates(bot_token: str, offset: int | None) -> list[dict]:
    endpoint = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    payload = {"timeout": 0}
    if offset is not None:
        payload["offset"] = offset
    response = requests.get(endpoint, params=payload, timeout=30)
    response.raise_for_status()
    body = response.json()
    return body.get("result", [])
