# NoFomo RSS Daily Digest V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python CLI that fetches RSS sources once per day, deduplicates and summarizes new items, highlights keyword matches, pushes a Telegram daily digest, and records Telegram feedback commands.

**Architecture:** The system is a file-backed batch pipeline with two CLI entrypoints: `run-digest` for the fetch-to-report flow and `sync-feedback` for Telegram feedback ingestion. Core processing is split into focused modules for configuration, feed ingestion, item normalization, keyword highlighting, report persistence, Telegram delivery, and feedback parsing so each stage can be tested independently and failures can be isolated without a long-running service.

**Tech Stack:** Python 3.12, `feedparser`, `PyYAML`, `requests`, `beautifulsoup4`, `pytest`, standard library `argparse`, `dataclasses`, `hashlib`, `json`, `logging`, `pathlib`

---

## File Structure

### Application files

- Create: `pyproject.toml` — project metadata, runtime dependencies, pytest config, console script entrypoint
- Create: `src/nofomo/__init__.py` — package marker and version export
- Create: `src/nofomo/main.py` — `run-digest` / `sync-feedback` CLI routing and orchestration
- Create: `src/nofomo/settings.py` — typed filesystem paths and runtime settings helpers
- Create: `src/nofomo/models.py` — dataclasses for sources, normalized items, reports, and feedback records
- Create: `src/nofomo/source_loader.py` — load/validate YAML source and keyword config
- Create: `src/nofomo/rss_fetcher.py` — fetch and parse RSS feeds into raw entry payloads
- Create: `src/nofomo/deduper.py` — build stable `item_id`, compute dedupe keys, read/write seen state
- Create: `src/nofomo/normalizer.py` — convert feed entries into `NormalizedItem` fields and strip HTML
- Create: `src/nofomo/summarizer.py` — generate `summary_short` and `summary_long` from RSS content
- Create: `src/nofomo/keyword_matcher.py` — keyword hit detection and highlight flagging
- Create: `src/nofomo/report_builder.py` — build overview + highlight/normal item sections for a `DailyReport`
- Create: `src/nofomo/report_store.py` — persist/read report JSON and append JSONL feedback records
- Create: `src/nofomo/telegram_sender.py` — Telegram Bot API calls for digest delivery
- Create: `src/nofomo/telegram_feedback.py` — parse `/like` and `/dislike`, fetch updates, advance offsets safely
- Create: `src/nofomo/logging_utils.py` — daily file logger setup and shared log formatting

### Config and data placeholders checked into repo

- Create: `config/sources.yaml` — example source definitions
- Create: `config/keywords.yaml` — example keyword list
- Create: `config/telegram.yaml` — example Telegram config template
- Create: `data/reports/.gitkeep` — keep reports directory in git
- Create: `data/logs/.gitkeep` — keep logs directory in git

### Tests

- Create: `tests/test_source_loader.py`
- Create: `tests/test_deduper.py`
- Create: `tests/test_normalizer.py`
- Create: `tests/test_summarizer.py`
- Create: `tests/test_keyword_matcher.py`
- Create: `tests/test_report_builder.py`
- Create: `tests/test_telegram_sender.py`
- Create: `tests/test_feedback_parser.py`
- Create: `tests/test_main_run_digest.py`
- Create: `tests/test_main_sync_feedback.py`

---

## Cross-Cutting Implementation Rules

- Persist `seen_items.json` **only after** Telegram digest delivery succeeds.
- Persist the daily report JSON **before** Telegram delivery so failed sends can be retried manually.
- Advance Telegram `offset` only after a specific update is parsed, validated, and recorded successfully.
- Keep all storage file-based for V1; no database, no daemon process, no webhook.
- Prefer dataclasses and plain functions over framework abstractions.
- Use TDD for each module: write a failing test, verify the failure, implement the minimum code, re-run the targeted test, then commit.

---

### Task 1: Bootstrap the package, settings, and core models

**Files:**
- Create: `pyproject.toml`
- Create: `src/nofomo/__init__.py`
- Create: `src/nofomo/settings.py`
- Create: `src/nofomo/models.py`
- Test: `tests/test_source_loader.py`

- [ ] **Step 1: Write the failing test for basic settings paths and source model loading shape**

```python
from pathlib import Path

from nofomo.models import SourceConfig
from nofomo.settings import AppPaths


def test_app_paths_resolve_from_project_root(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)

    assert paths.config_dir == tmp_path / "config"
    assert paths.data_dir == tmp_path / "data"
    assert paths.reports_dir == tmp_path / "data" / "reports"
    assert paths.logs_dir == tmp_path / "data" / "logs"


def test_source_config_defaults_enabled_true():
    source = SourceConfig(
        id="v2ex-hot",
        platform="v2ex",
        name="V2EX Hot",
        rss_url="https://example.com/feed.xml",
    )

    assert source.enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_source_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nofomo'`

- [ ] **Step 3: Write minimal project metadata and package bootstrap**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "nofomo"
version = "0.1.0"
description = "RSS daily digest CLI for Telegram"
requires-python = ">=3.12"
dependencies = [
  "beautifulsoup4>=4.12,<5",
  "feedparser>=6.0,<7",
  "PyYAML>=6.0,<7",
  "requests>=2.32,<3",
]

[project.optional-dependencies]
dev = ["pytest>=8.0,<9"]

[project.scripts]
nofomo = "nofomo.main:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
__version__ = "0.1.0"
```

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root_dir: Path
    config_dir: Path
    data_dir: Path
    reports_dir: Path
    logs_dir: Path
    seen_items_file: Path
    telegram_state_file: Path
    feedback_file: Path

    @classmethod
    def from_root(cls, root_dir: Path) -> "AppPaths":
        return cls(
            root_dir=root_dir,
            config_dir=root_dir / "config",
            data_dir=root_dir / "data",
            reports_dir=root_dir / "data" / "reports",
            logs_dir=root_dir / "data" / "logs",
            seen_items_file=root_dir / "data" / "seen_items.json",
            telegram_state_file=root_dir / "data" / "telegram_state.json",
            feedback_file=root_dir / "data" / "feedback.jsonl",
        )
```

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SourceConfig:
    id: str
    platform: str
    name: str
    rss_url: str
    enabled: bool = True


@dataclass(frozen=True)
class NormalizedItem:
    item_id: str
    source_id: str
    platform: str
    source_name: str
    title: str
    url: str
    published_at: str
    guid: str
    raw_summary: str
    normalized_text: str
    summary_short: str
    summary_long: str
    matched_keywords: list[str] = field(default_factory=list)
    is_highlight: bool = False


@dataclass(frozen=True)
class DailyReport:
    report_date: str
    generated_at: str
    total_new_items: int
    total_sources: int
    total_highlights: int
    failed_sources: list[str]
    highlights: list[NormalizedItem]
    normal_items: list[NormalizedItem]


@dataclass(frozen=True)
class FeedbackRecord:
    item_id: str
    report_date: str
    feedback_type: str
    source_id: str
    source_name: str
    matched_keywords: list[str]
    telegram_user_id: int
    telegram_chat_id: int
    telegram_message_id: int
    created_at: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_source_loader.py -v`
Expected: PASS for both tests

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/nofomo/__init__.py src/nofomo/settings.py src/nofomo/models.py tests/test_source_loader.py
git commit -m "chore: bootstrap nofomo package skeleton"
```

---

### Task 2: Implement YAML configuration loading for sources, keywords, and Telegram settings

**Files:**
- Modify: `src/nofomo/settings.py`
- Modify: `src/nofomo/models.py`
- Create: `src/nofomo/source_loader.py`
- Create: `config/sources.yaml`
- Create: `config/keywords.yaml`
- Create: `config/telegram.yaml`
- Test: `tests/test_source_loader.py`

- [ ] **Step 1: Write the failing tests for config loading**

```python
from pathlib import Path

from nofomo.source_loader import load_keywords, load_sources, load_telegram_config


def test_load_sources_returns_enabled_only(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
        sources:
          - id: v2ex-hot
            platform: v2ex
            name: V2EX Hot
            rss_url: https://example.com/v2ex.xml
            enabled: true
          - id: x-user
            platform: x
            name: X User
            rss_url: https://example.com/x.xml
            enabled: false
        """.strip(),
        encoding="utf-8",
    )

    sources = load_sources(config_dir / "sources.yaml")

    assert [source.id for source in sources] == ["v2ex-hot"]


def test_load_keywords_normalizes_case_and_strips_whitespace(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "keywords.yaml").write_text(
        "keywords:\n  - AI\n  - agent \n  -  automation\n",
        encoding="utf-8",
    )

    assert load_keywords(config_dir / "keywords.yaml") == ["ai", "agent", "automation"]


def test_load_telegram_config_reads_bot_token_and_chat_id(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "telegram.yaml").write_text(
        "bot_token: token123\nchat_id: chat456\n",
        encoding="utf-8",
    )

    telegram = load_telegram_config(config_dir / "telegram.yaml")

    assert telegram.bot_token == "token123"
    assert telegram.chat_id == "chat456"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_source_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nofomo.source_loader'`

- [ ] **Step 3: Extend models and implement config loading**

```python
@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str
```

```python
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
```

```yaml
sources:
  - id: v2ex-hot
    platform: v2ex
    name: V2EX Hot
    rss_url: https://example.com/v2ex.xml
    enabled: true
```

```yaml
keywords:
  - ai
  - agent
  - automation
```

```yaml
bot_token: REPLACE_ME
chat_id: REPLACE_ME
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_source_loader.py -v`
Expected: PASS for all config-loading tests

- [ ] **Step 5: Commit**

```bash
git add src/nofomo/models.py src/nofomo/source_loader.py config/sources.yaml config/keywords.yaml config/telegram.yaml tests/test_source_loader.py
git commit -m "feat: load source and telegram config from yaml"
```

---

### Task 3: Implement stable item identity and seen-state deduplication

**Files:**
- Create: `src/nofomo/deduper.py`
- Test: `tests/test_deduper.py`

- [ ] **Step 1: Write the failing deduplication tests**

```python
from pathlib import Path

from nofomo.deduper import build_item_id, compute_dedupe_key, filter_new_entries, load_seen_items, save_seen_items


def test_compute_dedupe_key_prefers_url_over_guid():
    entry = {
        "link": "https://example.com/post-1",
        "id": "guid-1",
        "title": "Hello",
        "published": "2026-04-11T08:00:00Z",
    }

    assert compute_dedupe_key("source-a", entry) == "url:https://example.com/post-1"


def test_build_item_id_is_stable_for_same_entry():
    entry = {
        "link": "https://example.com/post-1",
        "id": "guid-1",
        "title": "Hello",
        "published": "2026-04-11T08:00:00Z",
    }

    assert build_item_id("source-a", entry) == build_item_id("source-a", entry)


def test_filter_new_entries_skips_seen_items():
    entries = [
        {"link": "https://example.com/post-1", "title": "One", "published": "2026-04-11"},
        {"link": "https://example.com/post-2", "title": "Two", "published": "2026-04-11"},
    ]

    new_entries = filter_new_entries("source-a", entries, {"url:https://example.com/post-1"})

    assert [entry["title"] for entry in new_entries] == ["Two"]


def test_seen_items_round_trip(tmp_path: Path):
    seen_file = tmp_path / "seen_items.json"

    save_seen_items(seen_file, {"url:https://example.com/post-1"})

    assert load_seen_items(seen_file) == {"url:https://example.com/post-1"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_deduper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'nofomo.deduper'`

- [ ] **Step 3: Implement dedupe key generation and file persistence**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_deduper.py -v`
Expected: PASS for all four dedupe tests

- [ ] **Step 5: Commit**

```bash
git add src/nofomo/deduper.py tests/test_deduper.py
git commit -m "feat: add stable item id and dedupe state"
```

---

### Task 4: Normalize feed entries and generate rule-based summaries

**Files:**
- Create: `src/nofomo/normalizer.py`
- Create: `src/nofomo/summarizer.py`
- Test: `tests/test_normalizer.py`
- Test: `tests/test_summarizer.py`

- [ ] **Step 1: Write the failing normalization tests**

```python
from nofomo.normalizer import normalize_entry


def test_normalize_entry_strips_html_and_keeps_title():
    entry = {
        "title": "Hello World",
        "link": "https://example.com/post-1",
        "summary": "<p>AI <b>agent</b> update</p>",
        "id": "guid-1",
        "published": "2026-04-11T08:00:00Z",
    }

    item = normalize_entry(
        source_id="source-a",
        platform="x",
        source_name="X User",
        item_id="abc123def456",
        entry=entry,
    )

    assert item.title == "Hello World"
    assert item.raw_summary == "<p>AI <b>agent</b> update</p>"
    assert item.normalized_text == "AI agent update"
```

- [ ] **Step 2: Write the failing summarizer tests**

```python
from nofomo.summarizer import build_summaries


def test_build_summaries_prefers_existing_summary_text():
    short_text, long_text = build_summaries(
        raw_summary="<p>AI agent weekly recap with product launch details.</p>",
        normalized_text="AI agent weekly recap with product launch details.",
    )

    assert short_text == "AI agent weekly recap with product launch details."
    assert long_text == "AI agent weekly recap with product launch details."


def test_build_summaries_falls_back_to_trimmed_body_text():
    short_text, long_text = build_summaries(raw_summary="", normalized_text="One two three four five six seven eight nine ten eleven twelve")

    assert short_text.startswith("One two three")
    assert len(short_text) <= 120
    assert len(long_text) <= 280
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_normalizer.py tests/test_summarizer.py -v`
Expected: FAIL with missing `normalizer` / `summarizer` modules

- [ ] **Step 4: Implement normalization and summary generation**

```python
from bs4 import BeautifulSoup

from nofomo.models import NormalizedItem


def strip_html(value: str) -> str:
    if not value:
        return ""
    return " ".join(BeautifulSoup(value, "html.parser").get_text(" ").split())


def normalize_entry(source_id: str, platform: str, source_name: str, item_id: str, entry: dict) -> NormalizedItem:
    raw_summary = entry.get("summary") or entry.get("description") or ""
    normalized_text = strip_html(raw_summary or entry.get("title") or "")
    return NormalizedItem(
        item_id=item_id,
        source_id=source_id,
        platform=platform,
        source_name=source_name,
        title=(entry.get("title") or "(untitled)").strip(),
        url=(entry.get("link") or "").strip(),
        published_at=(entry.get("published") or entry.get("updated") or "").strip(),
        guid=(entry.get("id") or "").strip(),
        raw_summary=raw_summary,
        normalized_text=normalized_text,
        summary_short="",
        summary_long="",
    )
```

```python
from bs4 import BeautifulSoup


def _plain_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    return " ".join(BeautifulSoup(raw_text, "html.parser").get_text(" ").split())


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_summaries(raw_summary: str, normalized_text: str) -> tuple[str, str]:
    summary_text = _plain_text(raw_summary)
    base_text = summary_text or normalized_text
    short_text = _trim(base_text, 120)
    long_text = _trim(base_text, 280)
    return short_text, long_text
```

- [ ] **Step 5: Fill summary fields on normalized items with a focused helper**

```python
from dataclasses import replace

from nofomo.models import NormalizedItem
from nofomo.summarizer import build_summaries


def attach_summaries(item: NormalizedItem) -> NormalizedItem:
    summary_short, summary_long = build_summaries(item.raw_summary, item.normalized_text)
    return replace(item, summary_short=summary_short, summary_long=summary_long)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_normalizer.py tests/test_summarizer.py -v`
Expected: PASS for all normalization and summary tests

- [ ] **Step 7: Commit**

```bash
git add src/nofomo/normalizer.py src/nofomo/summarizer.py tests/test_normalizer.py tests/test_summarizer.py
git commit -m "feat: normalize feed entries and generate summaries"
```

---

### Task 5: Add keyword matching and report assembly

**Files:**
- Create: `src/nofomo/keyword_matcher.py`
- Create: `src/nofomo/report_builder.py`
- Test: `tests/test_keyword_matcher.py`
- Test: `tests/test_report_builder.py`

- [ ] **Step 1: Write the failing keyword matcher tests**

```python
from nofomo.keyword_matcher import apply_keywords
from nofomo.models import NormalizedItem


def make_item() -> NormalizedItem:
    return NormalizedItem(
        item_id="abc123def456",
        source_id="source-a",
        platform="x",
        source_name="X User",
        title="AI agent launch",
        url="https://example.com/post-1",
        published_at="2026-04-11T08:00:00Z",
        guid="guid-1",
        raw_summary="",
        normalized_text="AI agent launch with automation workflow",
        summary_short="AI agent launch with automation workflow",
        summary_long="AI agent launch with automation workflow",
    )


def test_apply_keywords_marks_highlight_when_keyword_matches():
    item = apply_keywords(make_item(), ["agent", "growth"])

    assert item.is_highlight is True
    assert item.matched_keywords == ["agent"]
```

- [ ] **Step 2: Write the failing report builder tests**

```python
from nofomo.models import NormalizedItem
from nofomo.report_builder import build_daily_report


def make_item(item_id: str, is_highlight: bool) -> NormalizedItem:
    return NormalizedItem(
        item_id=item_id,
        source_id="source-a",
        platform="x",
        source_name="X User",
        title=f"Title {item_id}",
        url=f"https://example.com/{item_id}",
        published_at="2026-04-11T08:00:00Z",
        guid=item_id,
        raw_summary="",
        normalized_text="AI agent launch",
        summary_short="AI agent launch",
        summary_long="AI agent launch",
        matched_keywords=["agent"] if is_highlight else [],
        is_highlight=is_highlight,
    )


def test_build_daily_report_splits_highlights_and_normal_items():
    report = build_daily_report(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        items=[make_item("one", True), make_item("two", False)],
        total_sources=1,
        failed_sources=["broken-feed"],
    )

    assert report.total_new_items == 2
    assert report.total_highlights == 1
    assert [item.item_id for item in report.highlights] == ["one"]
    assert [item.item_id for item in report.normal_items] == ["two"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_keyword_matcher.py tests/test_report_builder.py -v`
Expected: FAIL with missing matcher / report builder modules

- [ ] **Step 4: Implement keyword tagging**

```python
from dataclasses import replace

from nofomo.models import NormalizedItem


def apply_keywords(item: NormalizedItem, keywords: list[str]) -> NormalizedItem:
    haystack = " ".join([item.title, item.summary_short, item.summary_long, item.normalized_text]).lower()
    matched_keywords = [keyword for keyword in keywords if keyword in haystack]
    return replace(item, matched_keywords=matched_keywords, is_highlight=bool(matched_keywords))
```

- [ ] **Step 5: Implement daily report assembly**

```python
from nofomo.models import DailyReport, NormalizedItem


def build_daily_report(
    report_date: str,
    generated_at: str,
    items: list[NormalizedItem],
    total_sources: int,
    failed_sources: list[str],
) -> DailyReport:
    highlights = [item for item in items if item.is_highlight]
    normal_items = [item for item in items if not item.is_highlight]
    return DailyReport(
        report_date=report_date,
        generated_at=generated_at,
        total_new_items=len(items),
        total_sources=total_sources,
        total_highlights=len(highlights),
        failed_sources=failed_sources,
        highlights=highlights,
        normal_items=normal_items,
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_keyword_matcher.py tests/test_report_builder.py -v`
Expected: PASS for keyword and report assembly tests

- [ ] **Step 7: Commit**

```bash
git add src/nofomo/keyword_matcher.py src/nofomo/report_builder.py tests/test_keyword_matcher.py tests/test_report_builder.py
git commit -m "feat: highlight keyword hits and assemble daily report"
```

---

### Task 6: Persist reports and feedback archives on disk

**Files:**
- Create: `src/nofomo/report_store.py`
- Create: `data/reports/.gitkeep`
- Create: `data/logs/.gitkeep`
- Modify: `src/nofomo/models.py`
- Test: `tests/test_report_builder.py`
- Test: `tests/test_feedback_parser.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
import json
from pathlib import Path

from nofomo.models import DailyReport, FeedbackRecord, NormalizedItem
from nofomo.report_store import append_feedback_record, load_report_by_item_id, save_daily_report


def make_item(item_id: str) -> NormalizedItem:
    return NormalizedItem(
        item_id=item_id,
        source_id="source-a",
        platform="x",
        source_name="X User",
        title="AI agent launch",
        url="https://example.com/post-1",
        published_at="2026-04-11T08:00:00Z",
        guid=item_id,
        raw_summary="",
        normalized_text="AI agent launch",
        summary_short="AI agent launch",
        summary_long="AI agent launch",
    )


def test_save_daily_report_writes_json(tmp_path: Path):
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=1,
        total_sources=1,
        total_highlights=0,
        failed_sources=[],
        highlights=[],
        normal_items=[make_item("item-1")],
    )

    save_daily_report(tmp_path / "reports", report)

    payload = json.loads((tmp_path / "reports" / "2026-04-11.json").read_text(encoding="utf-8"))
    assert payload["report_date"] == "2026-04-11"
    assert payload["normal_items"][0]["item_id"] == "item-1"


def test_append_feedback_record_writes_json_line(tmp_path: Path):
    record = FeedbackRecord(
        item_id="item-1",
        report_date="2026-04-11",
        feedback_type="like",
        source_id="source-a",
        source_name="X User",
        matched_keywords=["agent"],
        telegram_user_id=1,
        telegram_chat_id=2,
        telegram_message_id=3,
        created_at="2026-04-11T10:00:00Z",
    )

    append_feedback_record(tmp_path / "feedback.jsonl", record)

    lines = (tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["feedback_type"] == "like"


def test_load_report_by_item_id_finds_item_in_saved_archive(tmp_path: Path):
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=1,
        total_sources=1,
        total_highlights=0,
        failed_sources=[],
        highlights=[],
        normal_items=[make_item("item-1")],
    )
    save_daily_report(tmp_path / "reports", report)

    found = load_report_by_item_id(tmp_path / "reports", "item-1")

    assert found is not None
    assert found["report_date"] == "2026-04-11"
    assert found["item"]["item_id"] == "item-1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_report_builder.py tests/test_feedback_parser.py -v`
Expected: FAIL with missing `report_store` helpers

- [ ] **Step 3: Implement JSON report and JSONL feedback storage**

```python
import json
from dataclasses import asdict
from pathlib import Path

from nofomo.models import DailyReport, FeedbackRecord


def save_daily_report(reports_dir: Path, report: DailyReport) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{report.report_date}.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(asdict(report), file, ensure_ascii=False, indent=2)
    return path


def append_feedback_record(path: Path, record: FeedbackRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def load_report_by_item_id(reports_dir: Path, item_id: str) -> dict | None:
    if not reports_dir.exists():
        return None
    for path in sorted(reports_dir.glob("*.json"), reverse=True):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for section in ("highlights", "normal_items"):
            for item in payload.get(section, []):
                if item.get("item_id") == item_id:
                    return {"report_date": payload["report_date"], "item": item}
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_report_builder.py tests/test_feedback_parser.py -v`
Expected: PASS for persistence-related tests

- [ ] **Step 5: Commit**

```bash
git add src/nofomo/report_store.py data/reports/.gitkeep data/logs/.gitkeep tests/test_report_builder.py tests/test_feedback_parser.py
git commit -m "feat: persist reports and feedback archives"
```

---

### Task 7: Implement Telegram digest sending with one-message-per-item formatting

**Files:**
- Create: `src/nofomo/telegram_sender.py`
- Test: `tests/test_telegram_sender.py`

- [ ] **Step 1: Write the failing Telegram formatting and sending tests**

```python
from nofomo.models import DailyReport, NormalizedItem, TelegramConfig
from nofomo.telegram_sender import build_digest_messages, send_messages


def make_item(item_id: str, highlight: bool) -> NormalizedItem:
    return NormalizedItem(
        item_id=item_id,
        source_id="source-a",
        platform="x",
        source_name="X User",
        title="AI agent launch",
        url="https://example.com/post-1",
        published_at="2026-04-11T08:00:00Z",
        guid=item_id,
        raw_summary="",
        normalized_text="AI agent launch",
        summary_short="Short summary",
        summary_long="Long summary",
        matched_keywords=["agent"] if highlight else [],
        is_highlight=highlight,
    )


def test_build_digest_messages_returns_overview_then_item_messages():
    report = DailyReport(
        report_date="2026-04-11",
        generated_at="2026-04-11T09:00:00Z",
        total_new_items=2,
        total_sources=1,
        total_highlights=1,
        failed_sources=["broken-feed"],
        highlights=[make_item("item-1", True)],
        normal_items=[make_item("item-2", False)],
    )

    messages = build_digest_messages(report)

    assert len(messages) == 3
    assert "今日概览" in messages[0]
    assert "/like item-1" in messages[1]
    assert "/dislike item-2" in messages[2]


def test_send_messages_posts_each_message(mocker):
    post = mocker.patch("nofomo.telegram_sender.requests.post")
    post.return_value.raise_for_status.return_value = None
    config = TelegramConfig(bot_token="token123", chat_id="chat456")

    send_messages(config, ["message one", "message two"])

    assert post.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_telegram_sender.py -v`
Expected: FAIL with missing `telegram_sender` module

- [ ] **Step 3: Add pytest mocker support and implement Telegram sender**

```toml
dev = [
  "pytest>=8.0,<9",
  "pytest-mock>=3.14,<4",
]
```

```python
import requests

from nofomo.models import DailyReport, NormalizedItem, TelegramConfig


def _format_item(item: NormalizedItem) -> str:
    summary = item.summary_long if item.is_highlight else item.summary_short
    keyword_line = f"命中关键词：{', '.join(item.matched_keywords)}\n" if item.matched_keywords else ""
    return (
        f"[{item.platform.upper()}] {item.source_name}\n"
        f"条目ID：{item.item_id}\n"
        f"标题：{item.title}\n"
        f"摘要：{summary}\n"
        f"{keyword_line}"
        f"原文：{item.url}\n"
        f"反馈：/like {item.item_id} | /dislike {item.item_id}"
    )


def build_digest_messages(report: DailyReport) -> list[str]:
    overview = (
        "今日概览\n"
        f"日期：{report.report_date}\n"
        f"新内容：{report.total_new_items}\n"
        f"来源数：{report.total_sources}\n"
        f"重点关注：{report.total_highlights}\n"
        f"失败来源：{len(report.failed_sources)}"
    )
    item_messages = [_format_item(item) for item in report.highlights + report.normal_items]
    return [overview, *item_messages]


def send_messages(config: TelegramConfig, messages: list[str]) -> None:
    endpoint = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
    for message in messages:
        response = requests.post(endpoint, json={"chat_id": config.chat_id, "text": message}, timeout=30)
        response.raise_for_status()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_telegram_sender.py -v`
Expected: PASS for both formatting and send tests

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/nofomo/telegram_sender.py tests/test_telegram_sender.py
git commit -m "feat: send digest messages to telegram"
```

---

### Task 8: Implement Telegram feedback parsing and safe offset advancement

**Files:**
- Create: `src/nofomo/telegram_feedback.py`
- Test: `tests/test_feedback_parser.py`

- [ ] **Step 1: Write the failing feedback parser tests**

```python
import json
from pathlib import Path

from nofomo.telegram_feedback import extract_feedback_command, load_offset, next_offset, save_offset


def test_extract_feedback_command_parses_like_command():
    update = {
        "update_id": 101,
        "message": {
            "message_id": 9,
            "date": 1712822400,
            "text": "/like item-1",
            "from": {"id": 1},
            "chat": {"id": 2},
        },
    }

    parsed = extract_feedback_command(update)

    assert parsed is not None
    assert parsed["feedback_type"] == "like"
    assert parsed["item_id"] == "item-1"


def test_extract_feedback_command_ignores_invalid_message():
    update = {"update_id": 102, "message": {"text": "hello"}}

    assert extract_feedback_command(update) is None


def test_offset_round_trip(tmp_path: Path):
    path = tmp_path / "telegram_state.json"

    save_offset(path, 105)

    assert load_offset(path) == 105
    assert next_offset(105) == 106
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_feedback_parser.py -v`
Expected: FAIL with missing `telegram_feedback` module

- [ ] **Step 3: Implement parsing and offset persistence helpers**

```python
import json
import re
from pathlib import Path

COMMAND_PATTERN = re.compile(r"^/(like|dislike)\s+([A-Za-z0-9_-]+)$")


def extract_feedback_command(update: dict) -> dict | None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    match = COMMAND_PATTERN.match(text)
    if not match:
        return None
    return {
        "update_id": update["update_id"],
        "feedback_type": match.group(1),
        "item_id": match.group(2),
        "telegram_user_id": message["from"]["id"],
        "telegram_chat_id": message["chat"]["id"],
        "telegram_message_id": message["message_id"],
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
```

- [ ] **Step 4: Add Telegram update fetching helper**

```python
import requests


def fetch_updates(bot_token: str, offset: int | None) -> list[dict]:
    endpoint = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    payload = {"timeout": 0}
    if offset is not None:
        payload["offset"] = offset
    response = requests.get(endpoint, params=payload, timeout=30)
    response.raise_for_status()
    body = response.json()
    return body.get("result", [])
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_feedback_parser.py -v`
Expected: PASS for parser and offset helpers

- [ ] **Step 6: Commit**

```bash
git add src/nofomo/telegram_feedback.py tests/test_feedback_parser.py
git commit -m "feat: parse telegram feedback commands"
```

---

### Task 9: Implement the `run-digest` orchestration path end-to-end

**Files:**
- Create: `src/nofomo/rss_fetcher.py`
- Modify: `src/nofomo/main.py`
- Modify: `src/nofomo/normalizer.py`
- Modify: `src/nofomo/report_store.py`
- Test: `tests/test_main_run_digest.py`

- [ ] **Step 1: Write the failing `run-digest` integration-style test**

```python
import json
from pathlib import Path

from nofomo.main import run_digest
from nofomo.models import TelegramConfig


def test_run_digest_saves_report_sends_messages_and_updates_seen(mocker, tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "data").mkdir()
    (root / "config" / "sources.yaml").write_text(
        "sources:\n  - id: source-a\n    platform: x\n    name: X User\n    rss_url: https://example.com/feed.xml\n",
        encoding="utf-8",
    )
    (root / "config" / "keywords.yaml").write_text("keywords:\n  - agent\n", encoding="utf-8")
    (root / "config" / "telegram.yaml").write_text("bot_token: token123\nchat_id: chat456\n", encoding="utf-8")

    mocker.patch("nofomo.main.fetch_feed_entries", return_value=[{
        "title": "AI agent launch",
        "link": "https://example.com/post-1",
        "summary": "<p>AI agent launch summary</p>",
        "id": "guid-1",
        "published": "2026-04-11T08:00:00Z",
    }])
    mocker.patch("nofomo.main.send_messages")

    run_digest(root)

    report = json.loads((root / "data" / "reports" / "2026-04-11.json").read_text(encoding="utf-8"))
    seen_items = json.loads((root / "data" / "seen_items.json").read_text(encoding="utf-8"))

    assert report["total_new_items"] == 1
    assert len(seen_items) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main_run_digest.py -v`
Expected: FAIL with missing `run_digest` / `fetch_feed_entries` orchestration code

- [ ] **Step 3: Implement feed fetching helper**

```python
import feedparser


def fetch_feed_entries(rss_url: str) -> list[dict]:
    parsed = feedparser.parse(rss_url)
    return [dict(entry) for entry in parsed.entries]
```

- [ ] **Step 4: Implement `run_digest` orchestration with safe write order**

```python
from datetime import UTC, datetime
from pathlib import Path

from nofomo.deduper import build_item_id, compute_dedupe_key, filter_new_entries, load_seen_items, save_seen_items
from nofomo.keyword_matcher import apply_keywords
from nofomo.normalizer import attach_summaries, normalize_entry
from nofomo.report_builder import build_daily_report
from nofomo.report_store import save_daily_report
from nofomo.rss_fetcher import fetch_feed_entries
from nofomo.settings import AppPaths
from nofomo.source_loader import load_keywords, load_sources, load_telegram_config
from nofomo.telegram_sender import build_digest_messages, send_messages


def run_digest(root_dir: Path) -> None:
    paths = AppPaths.from_root(root_dir)
    sources = load_sources(paths.config_dir / "sources.yaml")
    keywords = load_keywords(paths.config_dir / "keywords.yaml")
    telegram = load_telegram_config(paths.config_dir / "telegram.yaml")
    seen_items = load_seen_items(paths.seen_items_file)

    processed_items = []
    new_seen_keys = set()
    failed_sources = []

    for source in sources:
        try:
            entries = fetch_feed_entries(source.rss_url)
            new_entries = filter_new_entries(source.id, entries, seen_items)
            for entry in new_entries:
                item = normalize_entry(
                    source_id=source.id,
                    platform=source.platform,
                    source_name=source.name,
                    item_id=build_item_id(source.id, entry),
                    entry=entry,
                )
                item = attach_summaries(item)
                item = apply_keywords(item, keywords)
                processed_items.append(item)
                new_seen_keys.add(compute_dedupe_key(source.id, entry))
        except Exception:
            failed_sources.append(source.id)

    now = datetime.now(UTC)
    report = build_daily_report(
        report_date=now.date().isoformat(),
        generated_at=now.isoformat(),
        items=processed_items,
        total_sources=len(sources),
        failed_sources=failed_sources,
    )
    save_daily_report(paths.reports_dir, report)
    send_messages(telegram, build_digest_messages(report))
    save_seen_items(paths.seen_items_file, seen_items | new_seen_keys)
```

- [ ] **Step 5: Add a CLI `main()` wrapper**

```python
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["run-digest", "sync-feedback"])
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()
    if args.command == "run-digest":
        run_digest(root_dir)
    else:
        sync_feedback(root_dir)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_main_run_digest.py -v`
Expected: PASS and report JSON + seen state written under `tmp_path/data`

- [ ] **Step 7: Commit**

```bash
git add src/nofomo/rss_fetcher.py src/nofomo/main.py tests/test_main_run_digest.py
git commit -m "feat: orchestrate daily digest pipeline"
```

---

### Task 10: Implement the `sync-feedback` orchestration path and item validation against saved reports

**Files:**
- Modify: `src/nofomo/main.py`
- Modify: `src/nofomo/report_store.py`
- Modify: `src/nofomo/telegram_feedback.py`
- Test: `tests/test_main_sync_feedback.py`

- [ ] **Step 1: Write the failing `sync-feedback` integration-style test**

```python
import json
from pathlib import Path

from nofomo.main import sync_feedback


def test_sync_feedback_appends_valid_feedback_and_advances_offset(mocker, tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "data" / "reports").mkdir(parents=True)
    (root / "config" / "telegram.yaml").write_text("bot_token: token123\nchat_id: chat456\n", encoding="utf-8")
    (root / "data" / "reports" / "2026-04-11.json").write_text(
        json.dumps({
            "report_date": "2026-04-11",
            "generated_at": "2026-04-11T09:00:00Z",
            "total_new_items": 1,
            "total_sources": 1,
            "total_highlights": 1,
            "failed_sources": [],
            "highlights": [{
                "item_id": "item-1",
                "source_id": "source-a",
                "source_name": "X User",
                "matched_keywords": ["agent"],
            }],
            "normal_items": [],
        }),
        encoding="utf-8",
    )
    mocker.patch("nofomo.main.fetch_updates", return_value=[{
        "update_id": 101,
        "message": {
            "message_id": 9,
            "date": 1712822400,
            "text": "/like item-1",
            "from": {"id": 1},
            "chat": {"id": 2},
        },
    }])

    sync_feedback(root)

    lines = (root / "data" / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
    state = json.loads((root / "data" / "telegram_state.json").read_text(encoding="utf-8"))

    assert json.loads(lines[0])["item_id"] == "item-1"
    assert state["offset"] == 102
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main_sync_feedback.py -v`
Expected: FAIL with missing `sync_feedback` implementation

- [ ] **Step 3: Implement `sync_feedback` with validation against archived reports**

```python
from datetime import UTC, datetime

from nofomo.models import FeedbackRecord
from nofomo.report_store import append_feedback_record, load_report_by_item_id
from nofomo.source_loader import load_telegram_config
from nofomo.telegram_feedback import extract_feedback_command, fetch_updates, load_offset, next_offset, save_offset


def sync_feedback(root_dir: Path) -> None:
    paths = AppPaths.from_root(root_dir)
    telegram = load_telegram_config(paths.config_dir / "telegram.yaml")
    offset = load_offset(paths.telegram_state_file)
    updates = fetch_updates(telegram.bot_token, offset)

    for update in updates:
        parsed = extract_feedback_command(update)
        if parsed is None:
            continue

        found = load_report_by_item_id(paths.reports_dir, parsed["item_id"])
        if found is None:
            continue

        item = found["item"]
        record = FeedbackRecord(
            item_id=item["item_id"],
            report_date=found["report_date"],
            feedback_type=parsed["feedback_type"],
            source_id=item["source_id"],
            source_name=item["source_name"],
            matched_keywords=item.get("matched_keywords", []),
            telegram_user_id=parsed["telegram_user_id"],
            telegram_chat_id=parsed["telegram_chat_id"],
            telegram_message_id=parsed["telegram_message_id"],
            created_at=datetime.fromtimestamp(parsed["created_at"], UTC).isoformat(),
        )
        append_feedback_record(paths.feedback_file, record)
        save_offset(paths.telegram_state_file, next_offset(parsed["update_id"]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_main_sync_feedback.py -v`
Expected: PASS and valid feedback appended with offset `102`

- [ ] **Step 5: Commit**

```bash
git add src/nofomo/main.py tests/test_main_sync_feedback.py
git commit -m "feat: sync telegram feedback into local archive"
```

---

### Task 11: Add daily logging and verify the full test suite

**Files:**
- Create: `src/nofomo/logging_utils.py`
- Modify: `src/nofomo/main.py`
- Test: `tests/test_main_run_digest.py`
- Test: `tests/test_main_sync_feedback.py`

- [ ] **Step 1: Write the failing logging test**

```python
from pathlib import Path

from nofomo.logging_utils import configure_logger


def test_configure_logger_creates_daily_log_file(tmp_path: Path):
    logger = configure_logger(tmp_path, "2026-04-11")
    logger.info("hello")

    assert (tmp_path / "2026-04-11.log").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_main_run_digest.py -k logger -v`
Expected: FAIL with missing `logging_utils` module

- [ ] **Step 3: Implement daily file logging and wire it into both entrypoints**

```python
import logging
from pathlib import Path


def configure_logger(logs_dir: Path, log_date: str) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"nofomo.{log_date}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(logs_dir / f"{log_date}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
```

```python
from nofomo.logging_utils import configure_logger


now = datetime.now(UTC)
logger = configure_logger(paths.logs_dir, now.date().isoformat())
logger.info("run-digest started")
```

```python
offset = load_offset(paths.telegram_state_file)
logger.info("sync-feedback started with offset=%s", offset)
```

- [ ] **Step 4: Run the full test suite**

Run: `python -m pytest -v`
Expected: PASS for all unit and orchestration tests

- [ ] **Step 5: Smoke-test both CLI commands locally with example config**

Run: `python -m nofomo.main run-digest --root .`
Expected: Creates `data/reports/<today>.json` before Telegram send; if Telegram credentials are placeholders, run should fail at send step without writing `seen_items.json`

Run: `python -m nofomo.main sync-feedback --root .`
Expected: Reads `data/telegram_state.json` if present, ignores invalid commands, appends valid feedback lines to `data/feedback.jsonl`

- [ ] **Step 6: Commit**

```bash
git add src/nofomo/logging_utils.py src/nofomo/main.py tests/test_main_run_digest.py tests/test_main_sync_feedback.py
git commit -m "feat: add daily logging and finalize v1 cli flows"
```

---

## Verification Checklist

- `python -m pytest -v`
- `python -m nofomo.main run-digest --root .`
- `python -m nofomo.main sync-feedback --root .`
- Confirm `data/reports/<date>.json` exists after `run-digest`
- Confirm `data/feedback.jsonl` receives one JSON object per valid feedback command
- Confirm `data/telegram_state.json` only advances after successful record writes
- Confirm `data/seen_items.json` is not updated when Telegram sending fails

## Notes for the implementing engineer

- Keep `run-digest` failure handling narrow: catch source-level fetch failures so one bad feed does not block the rest, but do not swallow the final Telegram send failure because the caller needs the non-zero exit.
- Keep `sync-feedback` idempotent by validating `item_id` against archived reports and only then appending feedback + advancing offset.
- Do not add webhook support, inline keyboards, a database, or automatic keyword learning in this plan; all are explicitly out of scope for V1.
