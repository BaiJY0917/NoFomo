# NoFomo - RSS Daily Digest

A local Python CLI that fetches RSS sources once per day, deduplicates and summarizes new items, highlights keyword matches, pushes a Telegram daily digest, and records Telegram feedback commands.

## Features

- **RSS Feed Monitoring**: Fetch and parse multiple RSS sources
- **Smart Deduplication**: Track seen items across sources with stable IDs
- **Keyword Highlighting**: Mark items matching your keyword list
- **Telegram Integration**: Daily digest delivery and feedback collection
- **File-Based Storage**: No database required, all data stored locally in JSON/YAML

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd NoFomo

# Install dependencies
pip install -e .
```

## Configuration

### 1. Configure RSS Sources

Edit `config/sources.yaml`:

```yaml
sources:
  - id: v2ex-hot
    platform: v2ex
    name: V2EX Hot
    rss_url: https://www.v2ex.com/index.xml
    enabled: true

  - id: indie-hackers
    platform: indie-hackers
    name: Indie Hackers
    rss_url: https://indiehackers.com/feed
    enabled: true
```

### 2. Configure Keywords

Edit `config/keywords.yaml`:

```yaml
keywords:
  - AI
  - agent
  - productivity
  - automation
```

### 3. Configure Telegram

Edit `config/telegram.yaml`:

```yaml
bot_token: YOUR_BOT_TOKEN
chat_id: YOUR_CHAT_ID
```

To get your bot token, talk to [@BotFather](https://t.me/botfather) on Telegram.

## Usage

### Run Daily Digest

Generate and send today's digest:

```bash
nofomo run-digest
```

Or with Python:

```bash
python -m nofomo.main run-digest
```

This will:
1. Fetch all enabled RSS sources
2. Filter out already-seen items
3. Normalize and summarize content
4. Match against keywords and mark highlights
5. Build and save daily report
6. Send digest to Telegram
7. Update seen items list

### Sync Feedback

Collect feedback from Telegram:

```bash
nofomo sync-feedback
```

This will:
1. Fetch recent updates from Telegram Bot API
2. Parse `/like` and `/dislike` commands
3. Record feedback to local archive
4. Update offset to avoid reprocessing

### Telegram Commands

When reading the digest, reply with:

- `/like <item_id>` - Mark an item as liked
- `/dislike <item_id>` - Mark an item as disliked

Then run `nofomo sync-feedback` to record your feedback.

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Project Structure

```
NoFomo/
├── config/           # YAML configuration files
├── data/            # Local data storage
│   ├── reports/     # Daily report archives
│   └── logs/        # Application logs
├── src/nofomo/      # Main source code
│   ├── main.py      # CLI entry point
│   ├── models.py    # Data structures
│   ├── rss_fetcher.py
│   ├── deduper.py
│   ├── normalizer.py
│   ├── summarizer.py
│   ├── keyword_matcher.py
│   ├── report_builder.py
│   ├── telegram_sender.py
│   └── telegram_feedback.py
└── tests/           # Unit tests
```

## Architecture

NoFomo uses a file-backed batch pipeline architecture:

- **No daemon processes** - Runs on-demand via CLI
- **No database** - All state stored in JSON/YAML files
- **No webhooks** - Telegram feedback pulled on-demand
- **Fail-safe** - Errors logged, failed sources reported, partial progress preserved

## Tech Stack

- Python 3.12+
- feedparser - RSS parsing
- PyYAML - Configuration
- requests - HTTP requests
- beautifulsoup4 - HTML parsing
- pytest - Testing

## License

MIT
