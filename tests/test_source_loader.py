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
