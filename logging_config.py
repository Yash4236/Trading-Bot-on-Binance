"""
Logging configuration for the trading bot.
Sets up both file and console handlers with appropriate formatting.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the root logger for the trading bot.

    Args:
        log_dir: Directory where log files will be stored.
        log_level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger("trading_bot")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler — captures everything at DEBUG and above
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler — only INFO and above to avoid noise
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging initialised — writing to %s", log_filename)
    return logger
