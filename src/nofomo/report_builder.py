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
