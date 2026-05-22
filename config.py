"""
config.py — Загрузка конфигурации из .env файла и переменных окружения.

Использует python-dotenv для чтения .env.
Все параметры имеют значения по умолчанию.

Пример использования:
    >>> from config import load_config
    >>> cfg = load_config()
    >>> cfg.deepseek_api_key
    'sk-...'
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Неизменяемый объект конфигурации парсера.

    Attributes:
        start_url: Стартовый URL для обхода.
        max_depth: Максимальная глубина обхода.
        delay_seconds: Задержка между HTTP-запросами (сек).
        timeout_seconds: Таймаут загрузки страницы (сек).
        deepseek_api_key: API-ключ DeepSeek.
        deepseek_model: Модель DeepSeek (deepseek-chat).
        output_file: Путь к выходному Excel-файлу.
        log_file: Путь к файлу лога.
        max_text_length: Макс. длина текста страницы для API (символов).
        retry_attempts: Количество повторных попыток при ошибках.
    """

    start_url: str = "https://it-kirov.info/"
    max_depth: int = 5
    delay_seconds: float = 1.0
    timeout_seconds: int = 10
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    output_file: str = "output/it_kirov_analysis.xlsx"
    log_file: str = "parser.log"
    max_text_length: int = 8000
    retry_attempts: int = 2


def _resolve_env_path(env_path: str | None) -> str:
    """Определяет путь к .env файлу.

    Args:
        env_path: Явно указанный путь или None.

    Returns:
        Абсолютный путь к .env файлу.
    """
    if env_path is not None:
        return env_path
    return str(Path.cwd() / ".env")


def load_config(env_path: str | None = None) -> Config:
    """
    Загружает конфигурацию из .env (или указанного пути),
    затем дополняет из переменных окружения (переопределяют .env).

    Порядок приоритета:
        1. Переменные окружения (export KEY=val)
        2. Файл .env
        3. Значения по умолчанию из Config

    Args:
        env_path: Путь к .env файлу (опционально).
                  По умолчанию: ./.env

    Returns:
        Объект Config с загруженными параметрами.

    Note:
        Если .env не найден, выдаётся предупреждение в лог,
        и используются значения по умолчанию.
    """
    dotenv_path = _resolve_env_path(env_path)

    if not Path(dotenv_path).is_file():
        logging.warning("Файл .env не найден: %s. Использую значения по умолчанию.", dotenv_path)
        logging.warning("Скопируйте .env.example в .env и заполните ключи: cp .env.example .env")

    load_dotenv(dotenv_path=dotenv_path, override=False)

    return Config(
        start_url=os.getenv("START_URL", Config.start_url),
        max_depth=int(os.getenv("MAX_DEPTH", str(Config.max_depth))),
        delay_seconds=float(os.getenv("DELAY_SECONDS", str(Config.delay_seconds))),
        timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", str(Config.timeout_seconds))),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", Config.deepseek_api_key),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", Config.deepseek_model),
        output_file=os.getenv("OUTPUT_FILE", Config.output_file),
        log_file=os.getenv("LOG_FILE", Config.log_file),
        max_text_length=int(os.getenv("MAX_TEXT_LENGTH", str(Config.max_text_length))),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", str(Config.retry_attempts))),
    )
