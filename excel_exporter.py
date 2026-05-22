"""
excel_exporter.py — Сохранение результатов в Excel-файл.

Два листа:
  1. "Анализ страниц" — DataFrame с анализами
  2. "Дерево сайта" — иерархический список URL
"""

from pathlib import Path

import pandas as pd

from config import Config
from logger import setup_logger
from tree_builder import build_tree


def export_to_excel(
    df: pd.DataFrame,
    links_dict: dict[str, list[str]],
    config: Config,
) -> str:
    """
    Экспортирует результаты в Excel-файл.

    Args:
        df: DataFrame с колонками [Дата анализа, URL, Выжимка DeepSeek]
        links_dict: словарь связей для построения дерева
        config: конфигурация

    Returns:
        путь к сохранённому файлу
    """
    logger = setup_logger("excel_exporter", config.log_file)
    logger.info("Экспорт результатов в Excel: %s", config.output_file)

    # Создаём директорию для output, если её нет
    output_path = Path(config.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Строим дерево
    tree_lines = build_tree(links_dict)
    tree_df = pd.DataFrame(tree_lines, columns=["URL"])

    # Записываем в Excel
    with pd.ExcelWriter(
        str(output_path),
        engine="openpyxl",
        datetime_format="YYYY-MM-DD HH:MM",
    ) as writer:
        df.to_excel(writer, sheet_name="Анализ страниц", index=False)
        tree_df.to_excel(writer, sheet_name="Дерево сайта", index=False)

        # Настройка ширины колонок
        workbook = writer.book
        for sheet_name in ["Анализ страниц", "Дерево сайта"]:
            ws = workbook[sheet_name]
            for column_cells in ws.columns:
                max_length = 0
                col_letter = column_cells[0].column_letter
                for cell in column_cells:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                # Ограничиваем ширину
                adjusted_width = min(max_length + 2, 80)
                ws.column_dimensions[col_letter].width = adjusted_width

    logger.info("Excel-файл сохранён: %s", output_path.resolve())
    return str(output_path)
