import argparse
from datetime import UTC, datetime
from pathlib import Path

from nofomo.deduper import build_item_id, compute_dedupe_key, filter_new_entries, load_seen_items, save_seen_items
from nofomo.keyword_matcher import apply_keywords
from nofomo.logging_utils import configure_logger
from nofomo.models import FeedbackRecord
from nofomo.normalizer import attach_summaries, normalize_entry
from nofomo.report_builder import build_daily_report
from nofomo.report_store import append_feedback_record, load_report_by_item_id, save_daily_report
from nofomo.rss_fetcher import fetch_feed_entries
from nofomo.settings import AppPaths
from nofomo.source_loader import load_keywords, load_sources, load_telegram_config
from nofomo.telegram_feedback import extract_feedback_command, fetch_updates, load_offset, next_offset, save_offset
from nofomo.telegram_sender import build_digest_messages, send_messages


def run_digest(root_dir: Path) -> None:
    paths = AppPaths.from_root(root_dir)
    now = datetime.now(UTC)
    logger = configure_logger(paths.logs_dir, now.date().isoformat())
    logger.info("run-digest started")
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
    logger.info("processed %d items from %d sources", len(processed_items), len(sources))
    report = build_daily_report(
        report_date=now.date().isoformat(),
        generated_at=now.isoformat(),
        items=processed_items,
        total_sources=len(sources),
        failed_sources=failed_sources,
    )
    save_daily_report(paths.reports_dir, report)
    logger.info("report saved, sending to telegram")
    send_messages(telegram, build_digest_messages(report))
    save_seen_items(paths.seen_items_file, seen_items | new_seen_keys)
    logger.info("run-digest complete")


def sync_feedback(root_dir: Path) -> None:
    paths = AppPaths.from_root(root_dir)
    now = datetime.now(UTC)
    logger = configure_logger(paths.logs_dir, now.date().isoformat())
    telegram = load_telegram_config(paths.config_dir / "telegram.yaml")
    offset = load_offset(paths.telegram_state_file)
    logger.info("sync-feedback started with offset=%s", offset)
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
        logger.info("recorded feedback %s for item %s", parsed["feedback_type"], parsed["item_id"])


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


if __name__ == "__main__":
    main()
