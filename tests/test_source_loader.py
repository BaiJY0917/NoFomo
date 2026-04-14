from pathlib import Path

from nofomo.models import SourceConfig
from nofomo.settings import AppPaths
from nofomo.source_loader import load_keywords, load_sources, load_telegram_config


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
