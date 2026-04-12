import hashlib
import json
from pathlib import Path


def compute_dedupe_key(source_id: str, entry: dict) -> str:
    link = (entry.get("link") or "").strip()
    guid = (entry.get("id") or "").strip()
    title = (entry.get("title") or "").strip()
    published = (entry.get("published") or entry.get("updated") or "").strip()

    if link:
        return f"url:{link}"
    if guid:
        return f"guid:{source_id}:{guid}"
    return f"fallback:{source_id}:{title}:{published}"


def build_item_id(source_id: str, entry: dict) -> str:
    link = (entry.get("link") or "").strip()
    guid = (entry.get("id") or "").strip()
    title = (entry.get("title") or "").strip()
    published = (entry.get("published") or entry.get("updated") or "").strip()
    base = f"{source_id}|{link}|{guid}|{title}|{published}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def filter_new_entries(source_id: str, entries: list[dict], seen_items: set[str]) -> list[dict]:
    return [entry for entry in entries if compute_dedupe_key(source_id, entry) not in seen_items]


def load_seen_items(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as file:
        return set(json.load(file))


def save_seen_items(path: Path, seen_items: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(sorted(seen_items), file, ensure_ascii=False, indent=2)
