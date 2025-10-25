import logging
from typing import Optional
from app.core.config import settings


def configure_logging(level: Optional[int] = None) -> None:
    """
    Configure simple console logging for the application.
    """
    lvl = level or (logging.DEBUG if settings.DEBUG else logging.INFO)

    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(lvl)

    # If there are existing handlers, keep them (avoid duplicate handlers on reload).
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(lvl)
        sh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
        root.addHandler(sh)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger scoped to the given name (or the root logger).

    Usage: from app.core.logger import get_logger; log = get_logger(__name__)
    """
    return logging.getLogger(name or "vacation_agent")
