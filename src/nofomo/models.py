from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceConfig:
    id: str
    platform: str
    name: str
    rss_url: str
    enabled: bool = True


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str


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
