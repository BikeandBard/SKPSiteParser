"""
html_cleaner.py — Очистка HTML-контента.

Удаляет <script>, <style>, HTML-теги, лишние пробелы.
Обрезает текст до max_length символов.
"""

import re

from bs4 import BeautifulSoup


def clean_html(html: str, max_length: int = 8000) -> str:
    """
    Извлекает чистый текст из HTML.

    1. Парсит HTML через BeautifulSoup (lxml).
    2. Удаляет <script> и <style> блоки.
    3. Извлекает текст через .get_text() с разделителями-пробелами.
    4. Схлопывает множественные пробелы и пустые строки.
    5. Обрезает до max_length символов.

    Args:
        html: сырой HTML-код страницы
        max_length: максимальная длина выходного текста

    Returns:
        очищенный текст
    """
    if not html or not html.strip():
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Удаляем скрипты и стили
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    # Извлекаем текст
    text = soup.get_text(separator=" ", strip=True)

    # Схлопываем пробелы
    text = re.sub(r"\s+", " ", text).strip()

    # Обрезаем
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text
