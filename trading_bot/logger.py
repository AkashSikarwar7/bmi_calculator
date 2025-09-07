import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_rich_logger(name: str = "trading_bot", level: int | str = logging.INFO) -> logging.Logger:
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not any(isinstance(h, RichHandler) for h in logger.handlers):
        console = Console(stderr=True)
        handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger

