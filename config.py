"""
config.py — Загрузка конфигурации из .env файла и переменных окружения.

Использует python-dotenv для чтения config.env.
Все параметры имеют значения по умолчанию.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Неизменяемый объект конфигурации парсера."""

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


def load_config(env_path: str | None = None) -> Config:
    """
    Загружает конфигурацию из config.env (или указанного пути),
    затем дополняет из переменных окружения (переопределяют .env).

    Порядок приоритета:
        1. Переменные окружения (export KEY=val)
        2. Файл .env
        3. Значения по умолчанию из Config
    """
    load_dotenv(dotenv_path=env_path or os.path.join(os.getcwd(), "config.env"))

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
