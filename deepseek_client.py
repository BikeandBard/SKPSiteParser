"""
deepseek_client.py — Отправка текста в DeepSeek API для анализа.

Промпт: системное сообщение + текст страницы.
Возвращает краткую выжимку (2-3 предложения).
"""

import logging

import requests

from config import Config
from logger import setup_logger, retry_on_error

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = (
    "Ты — анализатор веб-страниц. "
    "Выдели главную тему, услуги или ключевую информацию "
    "страницы в 2-3 предложениях. "
    "Будь краток и информативен."
)


@retry_on_error(attempts=2, delay=2.0)
def _call_deepseek_api(api_key: str, text: str, model: str) -> str:
    """
    Отправляет запрос к DeepSeek API.

    Args:
        api_key: API-ключ
        text: очищенный текст страницы (до 8000 символов)
        model: название модели

    Returns:
        выжимка текста (строка)

    Raises:
        requests.exceptions.RequestException: при ошибке сети/HTTP
    """
    response = requests.post(
        DEEPSEEK_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Проанализируй:\n{text}"},
            ],
            "temperature": 0.3,
            "max_tokens": 300,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Извлекаем текст ответа
    choices = data.get("choices", [])
    if not choices:
        return "❌ Ошибка API: пустой ответ"
    message = choices[0].get("message", {})
    content = message.get("content", "")
    return content.strip()


def analyze_text(text: str, config: Config, logger: logging.Logger | None = None) -> str:
    """
    Анализирует текст страницы через DeepSeek API.

    Args:
        text: очищенный текст страницы
        config: конфигурация
        logger: логгер (опционально)

    Returns:
        выжимка текста или сообщение об ошибке
    """
    if not text or len(text.strip()) < 50:
        return "⚠️ Недостаточно данных (текст короче 50 символов)"

    if not config.deepseek_api_key or config.deepseek_api_key == "sk-xxx":
        return "⚠️ DeepSeek API ключ не настроен (config.env)"

    try:
        return _call_deepseek_api(config.deepseek_api_key, text, config.deepseek_model)
    except requests.exceptions.Timeout:
        msg = "❌ Ошибка API: таймаут"
        if logger:
            logger.error(msg)
        return msg
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        msg = f"❌ Ошибка API: HTTP {status}"
        if logger:
            logger.error(msg)
        return msg
    except requests.exceptions.RequestException as e:
        msg = f"❌ Ошибка API: {e}"
        if logger:
            logger.error(msg)
        return msg
    except Exception as e:
        msg = f"❌ Ошибка API: {e}"
        if logger:
            logger.error(msg)
        return msg
