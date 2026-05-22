"""
pipeline.py — Склейка пайплайна: URL → очистка → DeepSeek → результат.

Собирает DataFrame с колонками: Дата анализа, URL, Выжимка DeepSeek.
"""

import time
from datetime import datetime

import pandas as pd
import requests

from config import Config
from crawler import crawl
from deepseek_client import analyze_text
from html_cleaner import clean_html
from logger import setup_logger


def run_pipeline(config: Config) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """
    Запускает полный пайплайн.

    1. Обход сайта (crawler)
    2. Для каждого URL: очистка HTML → анализ через DeepSeek
    3. Сбор результатов в DataFrame

    Args:
        config: конфигурация

    Returns:
        (df, links_dict):
            df — DataFrame с колонками [Дата анализа, URL, Выжимка DeepSeek]
            links_dict — словарь связей для построения дерева
    """
    logger = setup_logger("pipeline", config.log_file)
    logger.info("=" * 60)
    logger.info("ЗАПУСК ПАЙПЛАЙНА")
    logger.info("=" * 60)

    # Шаг 1: Обход
    logger.info("Этап 1: Обход сайта %s", config.start_url)
    all_urls, links_dict = crawl(config)
    logger.info("Найдено URL: %d", len(all_urls))

    # Шаг 2: Анализ каждой страницы
    logger.info("Этап 2: Анализ страниц через DeepSeek API")
    rows: list[dict] = []

    for i, url in enumerate(all_urls, start=1):
        logger.info("[%d/%d] Анализирую: %s", i, len(all_urls), url)

        # Загружаем HTML
        try:
            resp = requests.get(
                url,
                timeout=config.timeout_seconds,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36"
                    ),
                    "Accept": "text/html",
                },
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error("Не удалось загрузить %s: %s", url, e)
            rows.append({
                "Дата анализа": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "URL": url,
                "Выжимка DeepSeek": f"❌ Ошибка загрузки: {e}",
            })
            continue

        # Очищаем HTML
        clean_text = clean_html(resp.text, config.max_text_length)

        if not clean_text:
            rows.append({
                "Дата анализа": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "URL": url,
                "Выжимка DeepSeek": "⚠️ Недостаточно данных (пустой HTML)",
            })
            continue

        # Анализируем через DeepSeek
        summary = analyze_text(clean_text, config, logger)

        rows.append({
            "Дата анализа": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "URL": url,
            "Выжимка DeepSeek": summary,
        })

        # Задержка между запросами к API
        time.sleep(config.delay_seconds)

    df = pd.DataFrame(rows, columns=["Дата анализа", "URL", "Выжимка DeepSeek"])
    logger.info("Пайплайн завершён. Проанализировано страниц: %d", len(df))
    return df, links_dict
