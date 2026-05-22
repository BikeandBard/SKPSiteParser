"""
logger.py — Логирование и обработка ошибок.

Записывает parser.log с датой, URL, статусом.
Поддерживает повтор запросов (retry) при ошибках 5xx.
"""

import logging
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import requests

R = TypeVar("R")
P = ParamSpec("P")


def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Настраивает логгер с выводом в файл и в консоль."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # Формат: 2025-01-15 12:00:00 | INFO | crawler | сообщение
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Консольный handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def retry_on_error(
    attempts: int = 2,
    delay: float = 1.0,
    backoff: float = 2.0,
    http_statuses: tuple[int, ...] = (500, 502, 503, 504),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для повторного выполнения при ошибках.

    Args:
        attempts: количество попыток (включая первую)
        delay: начальная задержка между попытками (сек)
        backoff: множитель задержки
        http_statuses: HTTP-статусы, при которых повторяем
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    last_exception = e
                    if e.response is not None and e.response.status_code in http_statuses:
                        if attempt < attempts:
                            time.sleep(current_delay)
                            current_delay *= backoff
                            continue
                    raise
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        requests.exceptions.RequestException) as e:
                    last_exception = e
                    if attempt < attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                        continue
                    raise
                except Exception as e:
                    # Не повторяем при других исключениях
                    raise

            # Если все попытки исчерпаны — пробрасываем последнее исключение
            if last_exception is not None:
                raise last_exception
            return None  # type: ignore[return-value]  # unreachable

        return wrapper

    return decorator
