from pathlib import Path

import yaml

from nofomo.models import SourceConfig, TelegramConfig


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_sources(path: Path) -> list[SourceConfig]:
    payload = _read_yaml(path)
    sources = payload.get("sources", [])
    return [
        SourceConfig(**source)
        for source in sources
        if source.get("enabled", True)
    ]


def load_keywords(path: Path) -> list[str]:
    payload = _read_yaml(path)
    return [keyword.strip().lower() for keyword in payload.get("keywords", []) if keyword.strip()]


def load_telegram_config(path: Path) -> TelegramConfig:
    payload = _read_yaml(path)
    return TelegramConfig(
        bot_token=payload["bot_token"],
        chat_id=str(payload["chat_id"]),
    )
