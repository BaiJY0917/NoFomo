import logging
from pathlib import Path


def configure_logger(logs_dir: Path, log_date: str) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"nofomo.{log_date}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(logs_dir / f"{log_date}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
