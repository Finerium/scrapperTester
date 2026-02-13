"""
Utility functions: retry decorator, random delays, logging setup.
"""
import os
import time
import random
import logging
import functools
from typing import Callable, Any

from config import MIN_DELAY, MAX_DELAY, MAX_RETRIES, RETRY_BACKOFF_BASE, LOG_DIR, LOG_FILE


def setup_logging(log_file: str = LOG_FILE, level: int = logging.INFO):
    """Configure logging to both file and console."""
    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def random_delay(min_sec: float = MIN_DELAY, max_sec: float = MAX_DELAY):
    """Sleep for a random duration between min_sec and max_sec."""
    delay = random.uniform(min_sec, max_sec)
    logging.getLogger(__name__).debug("Sleeping %.2f seconds", delay)
    time.sleep(delay)


def retry_on_failure(
    max_retries: int = MAX_RETRIES,
    backoff_base: float = RETRY_BACKOFF_BASE,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator: retry a function on failure with exponential backoff.
    Backoff schedule: backoff_base * (2 ** attempt)
    Example with base=5: 5s, 10s, 20s
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = backoff_base * (2 ** attempt)
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.0fs...",
                            attempt + 1, max_retries + 1, func.__name__, str(e), wait
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            "All %d attempts failed for %s: %s",
                            max_retries + 1, func.__name__, str(e)
                        )
            raise last_exception
        return wrapper
    return decorator
