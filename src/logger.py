from __future__ import annotations

import logging
from pathlib import Path

from .config_loader import LoggingConfig


def setup_logger(config: LoggingConfig) -> logging.Logger:
    logger = logging.getLogger("substack_reads")
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if config.log_to_file:
        log_dir = Path(config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "pipeline.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

