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
