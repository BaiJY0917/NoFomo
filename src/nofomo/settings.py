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
