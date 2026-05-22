#!/usr/bin/env python3
"""
main.py — Точка входа в приложение SiteParser.

Запускает полный пайплайн:
  1. Обход сайта (crawler)
  2. Анализ через DeepSeek (deepseek_client)
  3. Экспорт в Excel (excel_exporter)

Использование:
    # Убедитесь, что .env настроен:
    cp .env.example .env
    # Заполните DEEPSEEK_API_KEY в .env

    # Запуск с .env по умолчанию:
    python main.py

    # Запуск с кастомным конфигом:
    python main.py --config /path/to/custom.env
"""

import argparse
import sys

from config import load_config
from excel_exporter import export_to_excel
from logger import setup_logger
from pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Парсинг сайта it-kirov.info + анализ через DeepSeek"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Путь к файлу конфигурации (.env)",
    )
    args = parser.parse_args()

    # Загружаем конфигурацию
    config = load_config(args.config)
    logger = setup_logger("main", config.log_file)

    logger.info("=" * 60)
    logger.info("SiteParser v1.0 — MVP")
    logger.info("Целевой сайт: %s", config.start_url)
    logger.info("Макс. глубина: %d", config.max_depth)
    logger.info("Файл вывода: %s", config.output_file)
    logger.info("=" * 60)

    # Проверка API-ключа
    if not config.deepseek_api_key or config.deepseek_api_key == "sk-xxx":
        logger.warning("⚠️ DeepSeek API ключ не настроен! Анализ будет пропущен.")

    # Запуск пайплайна
    try:
        df, links_dict = run_pipeline(config)
    except KeyboardInterrupt:
        logger.info("Прерывание пользователем. Выход.")
        sys.exit(1)
    except Exception as e:
        logger.critical("Критическая ошибка пайплайна: %s", e, exc_info=True)
        sys.exit(2)

    # Экспорт в Excel
    try:
        output_path = export_to_excel(df, links_dict, config)
    except Exception as e:
        logger.critical("Ошибка экспорта в Excel: %s", e, exc_info=True)
        sys.exit(3)

    # Итог
    logger.info("=" * 60)
    logger.info("✅ УСПЕШНО ЗАВЕРШЕНО")
    logger.info("📄 Результат: %s", output_path)
    logger.info("📊 Проанализировано страниц: %d", len(df))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
