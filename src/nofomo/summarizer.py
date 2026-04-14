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
