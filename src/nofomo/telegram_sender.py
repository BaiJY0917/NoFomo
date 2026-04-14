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
